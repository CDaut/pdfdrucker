import re
import socket
import subprocess
import time
from threading import Thread


class Printerthread(Thread):
    def __init__(self):
        super().__init__()
        # make this a daemon thread
        self.daemon = True
        self.__queue = []

    def run(self):
        # main printing loop
        while True:
            # wait a few seconds if the queue is empty
            if len(self.__queue) == 0:
                time.sleep(5.0)
            else:
                printjob = self.get_first_job()
                print("Print job recieved. Name: " + printjob.pdfpath + ", user: " + printjob.username)

                # dispatch print job
                # get cups server hostname
                hostname = socket.gethostbyname('cups')
                # call lp
                from_stdout = str(subprocess.check_output('lp -h ' + hostname + ':631 -d ABH ' + printjob.pdfpath,
                                                          shell=True))
                # extract the real printjob id
                jobid = re.search('ABH-[0-9]+', from_stdout).group(0)

                # update the printjobs jobid
                printjob.jobid = jobid

    def enqueue(self, printjob):
        self.__queue.append(printjob)

    def get_first_job(self):
        return self.__queue.pop(0)
