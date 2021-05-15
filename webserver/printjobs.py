import socket

from bs4 import BeautifulSoup
from enum import Enum, auto
import requests


class JobStatus(Enum):
    COMPLETED = auto
    FAILED = auto
    PROCESSING = auto
    PENDING = auto


class Printjob:
    def __init__(self, username, pdfpath):
        self.jobid = None
        self.username = username
        self.pdfpath = pdfpath

    '''
    Method to get the print jobs status by fetching the HTML from cups and parsing it
    '''

    def fetch_status(self):
        # make request to site
        # get cups server hostname
        ip = socket.gethostbyname('cups')

        # make request and extract the table
        result = requests.get("http://" + ip + ":631/printers/ABH")
        parsed = BeautifulSoup(result.text, features='html.parser')
        jobtable = parsed.find("table", attrs={'summary': 'Job List'})



        print(jobtable)
        pass
