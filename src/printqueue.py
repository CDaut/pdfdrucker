import os
import re
import smtplib
import socket
import ssl
import subprocess
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Thread

import paramiko
from flask import render_template
from paramiko.sftp_client import SFTPClient

from printjobs import JobStatus
import app


class Printerthread(Thread):
    def __init__(self, config, logger, secret):
        super().__init__()
        # make this a daemon thread
        self.daemon = True
        self.__queue = []
        self.__config = config
        self.__logger = logger
        self.__secret = secret

    def run(self):
        # main printing loop
        while True:
            # wait a few seconds if the queue is empty
            if len(self.__queue) == 0:
                time.sleep(self.__config['check_for_new_job_interval'])
            else:
                # check if the queue is getting filled up
                if len(self.__queue) >= self.__config['queue_alert_threshold']:
                    self.notify_queue_full()
                self.handle_print_job()

    def handle_print_job(self):

        # connect to smb share and clear directory to ensure a clean starting state
        # connect to remote server via sftp
        transport = paramiko.Transport((self.__config['sftp_address'], 22))
        transport.banner_timeout = 60
        transport.connect(None, self.__secret['username'], self.__secret['sftp_password'])

        # create sftp connection
        sftp = SFTPClient.from_transport(transport)

        printjob = self.get_first_job()

        # dispatch print job
        # get cups server hostname
        hostname = socket.gethostbyname('cups')

        # save the start time
        printjob.starttime = time.time()

        # construct lp command
        cupsopts = ' -o fit-to-page'
        if os.environ['CUPS_PRINTER_MODEL_OPTION']:
            cupsopts += ' ' + os.environ['CUPS_PRINTER_MODEL_OPTION']

        if printjob.duplex:
            cupsopts += ' ' + os.environ['CUPS_DUPLEX_OPTION']
        else:
            cupsopts += ' ' + os.environ['CUPS_SIMPLEX_OPTION']

        if printjob.color:
            cupsopts += ' ' + os.environ['CUPS_COLOR_OPTION']
        else:
            cupsopts += ' ' + os.environ['CUPS_GREYSCALE_OPTION']

        if printjob.copies > 1:
            cupsopts += ' ' + os.environ['CUPS_COPY_OPTION'] + ' ' + str(printjob.copies)
        else:
            printjob.copies = 1

        cupsopts += ' -o PageSize=' + printjob.pagesize

        cmd = 'lp -h ' + hostname + ':631 -d ' + os.environ['CUPS_PRINTER_NAME'] + cupsopts + ' ' + printjob.pdfpath
        self.__logger.info('lp command: ' + cmd)

        # call lp
        from_stdout = str(subprocess.check_output(cmd, shell=True))
        # extract the real printjob id
        jobid = re.search('(ABH-)([0-9]+)', from_stdout).group(2)
        # update the printjobs jobid
        printjob.jobid = jobid

        self.__logger.info("Print job %s from user %s with %d pages and %s copies has been dispatched.", printjob.jobid,
                           printjob.username, printjob.numpages, printjob.copies)

        check_status = True

        while check_status:
            # sleep some time so we don't dos our own cups server
            time.sleep(float(self.__config['status_fetch_sleep_interval']))

            # fetch job status
            status_tupel = printjob.fetch_status()
            status = status_tupel[0]
            message = status_tupel[1]

            # handle different job status codes where something needs to be done
            if status is JobStatus.COMPLETED:
                printjob.completetime = time.time()
                check_status = False
                self.__logger.info('Completed compiling postscript for job %s by user %s within %d seconds.'
                                   '', jobid, printjob.username, printjob.completetime - printjob.starttime)
            elif status is JobStatus.FAILED:
                self.__logger.error('Job %s by user %s errored!', jobid, printjob.username)
                return  # return at this point because no smb share processing should be done
            elif status is JobStatus.UNKNOWN:
                self.__logger.error('Received unknown status code: ' + message)

        # get files in remote directory
        files = os.listdir('/print')

        # throw an error if more than tow files are present (.gitkeep and out.ps)
        if len(files) > 2:
            self.__logger.error('More than two files are present. Aborting.')
            return

        # failsafe to not shut down the printer thread if no file is found
        if len(files) == 0:
            self.__logger.error('No postscript file found. Aborting.')
            return

        # move the file to the correct user directory
        postscript_file_path = '/print/out.ps'

        filename = printjob.filename + '.ps'
        newpath = os.path.join('/home/sambashares/printjobs', printjob.username, filename)

        # check if userdir exists
        userdirs = sftp.listdir('/home/sambashares/printjobs')

        # create userdir if needed and set correct permissions
        if printjob.username not in userdirs:
            sftp.mkdir(os.path.join('/home/sambashares/printjobs', printjob.username))
            sftp.chmod(os.path.join('/home/sambashares/printjobs', printjob.username), 0o777)

        # use rename to move the file
        sftp.put(postscript_file_path, newpath)
        self.__logger.info('Moved file ' + postscript_file_path + ' to ' + printjob.username + '\'s printing queue.')

    def notify_queue_full(self):
        self.__logger.info('Sending an email alert because the queue exceeded the threshhold...')

        # create a new message
        message = MIMEMultipart()
        message['From'] = self.__config['from_address']
        message['To'] = self.__config['to_address']
        message['Subject'] = self.__config['email_subject']

        # add message body
        with app.get_context():
            rendered = render_template(
                'alert_email.html',
                limit=self.__config['queue_alert_threshold'],
                numjobs=self.get_queue_size(),
                numpages=self.get_page_sum(),
                running=self.is_alive()
            )

        message.attach(MIMEText(rendered, 'html'))

        # load and configure attatchment
        with open('serverlog.log', 'rb') as logfile:
            att = MIMEBase('application', 'octet-stream')
            att.set_payload(logfile.read())

        encoders.encode_base64(att)
        att.add_header(
            "Content-Disposition",
            f"attachment; filename= serverlog.log",
        )

        # attatch log file
        message.attach(att)

        # create security context
        context = ssl.create_default_context()

        # create secure smtp connection to the server and log in
        with smtplib.SMTP_SSL(
                self.__config['smtp_server_address'],
                self.__config['smtp_port'],
                context=context
        ) as server:
            server.login(self.__config['from_address'], self.__secret['mail_password'])

            # send the message
            server.sendmail(self.__config['from_address'], self.__config['to_address'], message.as_string())

    def enqueue(self, printjob):
        self.__queue.append(printjob)

    def get_first_job(self):
        return self.__queue.pop(0)

    def get_queue_size(self):
        return len(self.__queue)

    def clear_queue(self):
        self.__queue = []

    def get_page_sum(self):
        pages = 0

        for printjob in self.__queue:
            pages += printjob.numpages

        return pages
