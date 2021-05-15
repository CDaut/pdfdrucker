import os.path
import socket
from os.path import join
import time
from shutil import move

from flask import Flask, render_template, request
from yaml import YAMLError, safe_load

from validation import validate_pdf, validate_user
from printqueue import Printerthread
from printjobs import Printjob

app = Flask(__name__)

global CONFIG
global PRINTERTHREAD


@app.before_first_request
def setup():
    # try to load the config file
    with open('config.yml', 'r') as configfile:
        try:
            # load the config
            global CONFIG
            CONFIG = safe_load(configfile)
        except YAMLError as error:
            exit("Unable to load config: " + str(error))

    # generate, assign and dispatch a new printer thread
    global PRINTERTHREAD
    PRINTERTHREAD = Printerthread()
    PRINTERTHREAD.start()
    print("Dispatched printer Thread.")


def handle_get():
    return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'])


def handle_post():
    # validate the user data
    is_valid = validate_user(request.form)

    if is_valid != 'ISVALID':
        return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'], error=is_valid)

    # get the uploaded file and validate filename
    uploaded_file = request.files['pdffile']

    # save the file temporarily because PDFLoader might break it
    unixtime = int(time.time())
    username = request.form['username']
    temppath = CONFIG['temporary_storage']
    filename = join(temppath, username + '_' + str(unixtime) + '.pdf')

    # save the file
    uploaded_file.save(filename)

    # call the helper method to validate the pdf
    valid = validate_pdf(uploaded_file, CONFIG)

    if not valid == 'ISVALID':
        # remove file from tempdir
        os.remove(filename)

        return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'], error=valid)

    # at this point we know that the uploaded file is a valid pdf file

    # move uploaded pdffile to our print spooler
    spooler_dir = CONFIG['spooler_directory']
    newpath = join(spooler_dir, username + '_' + str(unixtime) + '.pdf')
    move(filename, newpath)

    # create a new printjob and enqueue it
    job = Printjob(username, newpath)
    PRINTERTHREAD.enqueue(job)

    return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'],
                           success='Ihre Datei wird nun verarbeitet. '
                                   + 'Bitte beachten sie, dass das Verarbeiten von großen '
                                   + 'PDFs unter Umständen mehrere Minuten dauern kann.')


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return handle_post()
    else:
        return handle_get()
