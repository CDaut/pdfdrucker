from bs4 import BeautifulSoup


class Printjob():
    def __init__(self, jobid, status):
        self.jobid = jobid
        self.status = status


def fromhtml(htmlstring):
    # parse the html and get the tables with the jobs
    parsed = BeautifulSoup(htmlstring)
    jobtable = parsed.find('TABLE', attrs={'summary': 'Job List'})
    print(jobtable)
