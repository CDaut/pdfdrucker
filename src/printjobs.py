import socket
import unicodedata
import os

from bs4 import BeautifulSoup
from enum import Enum
import requests


class JobStatus(Enum):
    COMPLETED = 0
    FAILED = 1
    PROCESSING = 2
    PENDING = 3
    HELD = 4
    UNKNOWN = 5


class Printjob:
    def __init__(self, username, filename, pdfpath, pages, duplex, color, pagesize, copies):
        self.username = username
        self.filename = filename
        self.pdfpath = pdfpath
        self.numpages = pages
        self.duplex = duplex
        self.color= color
        self.pagesize = pagesize
        self.copies = copies
        self.starttime = None
        self.completetime = None
        self.jobid = None

    '''
    Method to get the print jobs status by fetching the HTML from cups and parsing it
    '''

    def fetch_status(self):
        # make request to site
        # get cups server hostname
        ip = socket.gethostbyname('cups')

        # make request and extract the table
        result = requests.get("http://" + ip + ":631/printers/" + os.environ['CUPS_PRINTER_NAME'])
        parsed = BeautifulSoup(result.text, features='html.parser')
        jobtable = parsed.find("table", attrs={'summary': 'Job List'})

        # if no jobs are queued, printing was successful, because failed jobs will stay in the table
        if jobtable is None:
            return JobStatus.COMPLETED, ''

        headers = [header.text.lower() for header in jobtable.find_all('th')]
        results = [{headers[i]: cell for i, cell in enumerate(row.find_all('td'))}
                   for row in jobtable.find_all('tr')]

        # remove empty rows
        results.remove({})

        # check all rows for matching job ID and get status for that id
        job_found = False
        for row in results:
            jobid = row['id'].contents[1][1:]

            if int(jobid) == int(self.jobid):
                state = row['state']
                # extract the state information
                rawstatus = unicodedata.normalize('NFKC', state.text.replace('\n', '')).split(' ')[0]

                if rawstatus == 'pending':
                    return JobStatus.PENDING, ''
                elif rawstatus == 'stopped':
                    return JobStatus.FAILED, ''
                elif rawstatus == 'processing':
                    return JobStatus.PROCESSING, ''
                elif rawstatus == 'held':
                    return JobStatus.HELD, ''
                else:
                    return JobStatus.UNKNOWN, '"' + rawstatus + '"'

        # if the print job is not listed in the table anymnore, it can be marked as completed
        if not job_found:
            return JobStatus.COMPLETED, ''
