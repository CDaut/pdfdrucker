from bs4 import BeautifulSoup
from enum import Enum


class JobStatus(Enum):
    COMPLETED = 0
    FAILED = 1
    PROCESSING = 2


class Printjob:
    def __init__(self, username, pdfpath):
        self.jobid = None
        self.username = username
        self.pdfpath = pdfpath

    '''
    Method to get the print jobs status by fetching the HTML from cups and parsing it
    '''

    def update_status(self):
        # TODO: set status accoarding to the html returned from the site
        # after being parsed by BeautifulSoap
        pass
