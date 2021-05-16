import os
import re
import socket
import subprocess
import time
from threading import Thread

import paramiko
from paramiko.sftp_client import SFTPClient

from printjobs import JobStatus


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
                self.handle_print_job()

    def handle_print_job(self):

        # connect to smb share and clear directory to ensure a clean starting state
        # connect to remote server via sftp
        transport = paramiko.Transport((self.__config['sftp_address'], 22))
        transport.connect(None, self.__secret['username'], self.__secret['sftp_password'])

        # create sftp connection
        sftp = SFTPClient.from_transport(transport)

        pdf_printer_dir_path = os.path.join(self.__config['remote_dir'], 'pdfprinter')

        # list all files
        files = sftp.listdir(pdf_printer_dir_path)

        # delete all files
        for file in files:
            filepath = os.path.join(self.__config['remote_dir'], 'pdfprinter', file)
            sftp.remove(filepath)

        printjob = self.get_first_job()

        # dispatch print job
        # get cups server hostname
        hostname = socket.gethostbyname('cups')

        # save the start time
        printjob.starttime = time.time()

        # call lp
        from_stdout = str(subprocess.check_output('lp -h ' + hostname + ':631 -d ABH ' + printjob.pdfpath,
                                                  shell=True))
        # extract the real printjob id
        jobid = re.search('(ABH-)([0-9]+)', from_stdout).group(2)
        # update the printjobs jobid
        printjob.jobid = jobid

        self.__logger.info("Print job %s from user %s with %d pages has been dispatched.", printjob.jobid,
                           printjob.username, printjob.numpages)

        check_status = True

        while check_status:
            # sleep some time so we don't dos our own cups server
            time.sleep(float(self.__config['status_fetch_sleep_interval']))

            # fetch job status
            status = printjob.fetch_status()

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
                self.__logger.error('Received unknown status code')

        # get files in remote directory
        files = sftp.listdir(pdf_printer_dir_path)

        # throw an error if more than one file is present
        if len(files) > 1:
            self.__logger.error('More than two files are present. Aborting.')
            return

        # failsafe to not shut down the printer thread if no file is found
        if len(files) == 0:
            self.__logger.error('No postscript file found. Aborting.')
            return

        # move the file to the correct user directory
        postscript_file_path = os.path.join(pdf_printer_dir_path, files[0])

        newpath = os.path.join('/home/sambashares/printjobs', printjob.username, files[0])

        # check if userdir exists
        userdirs = sftp.listdir('/home/sambashares/printjobs')

        # create userdir if needed and set correct permissions
        if printjob.username not in userdirs:
            sftp.mkdir(os.path.join('/home/sambashares/printjobs', printjob.username))
            sftp.chmod(os.path.join('/home/sambashares/printjobs', printjob.username), 0o777)

        # use rename to move the file
        sftp.rename(postscript_file_path, newpath)
        self.__logger.info('Moved file ' + postscript_file_path + ' to ' + printjob.username + 's printing queue.')

    def enqueue(self, printjob):
        self.__queue.append(printjob)

    def get_first_job(self):
        return self.__queue.pop(0)

    def get_queue_size(self):
        return len(self.__queue)

    def get_page_sum(self):
        pages = 0

        for printjob in self.__queue:
            pages += printjob.numpages

        return pages
