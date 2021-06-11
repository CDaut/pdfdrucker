import os.path
from os.path import join
import time
from shutil import move

from flask import Flask, render_template, request
from yaml import YAMLError, safe_load

from validation import validate_pdf, validate_user, get_number_of_pages
from printqueue import Printerthread
from printjobs import Printjob

app = Flask(__name__)

global CONFIG
global SECRETS
global PRINTERTHREAD
global logger


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

    # try to load the secrets file
    with open('secrets.yml', 'r') as secretsfile:
        try:
            # load the config
            global SECRETS
            SECRETS = safe_load(secretsfile)
        except YAMLError as error:
            exit("Unable to load secrets.yml: " + str(error))

    # generate, assign and dispatch a new printer thread
    global PRINTERTHREAD
    PRINTERTHREAD = Printerthread(CONFIG, app.logger, SECRETS)
    PRINTERTHREAD.start()
    app.logger.info("Dispatched printer Thread.")


def handle_get():
    return render_template('index.html',
                           maxpdfsize=CONFIG['maxpdfsize'],
                           num_documents=PRINTERTHREAD.get_queue_size(),
                           num_pages=PRINTERTHREAD.get_page_sum())


def handle_post():
    # validate the user data
    is_valid = validate_user(request.form, CONFIG, SECRETS)

    if is_valid != 'ISVALID':
        return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'], error=is_valid,
                               num_documents=PRINTERTHREAD.get_queue_size(),
                               num_pages=PRINTERTHREAD.get_page_sum())

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

        return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'], error=valid,
                               num_documents=PRINTERTHREAD.get_queue_size(),
                               num_pages=PRINTERTHREAD.get_page_sum())

    # at this point we know that the uploaded file is a valid pdf file

    num_pages = get_number_of_pages(uploaded_file)

    # move uploaded pdffile to our print spooler
    spooler_dir = CONFIG['spooler_directory']
    newpath = join(spooler_dir, username + '_' + str(unixtime) + '.pdf')
    move(filename, newpath)

    # create a new printjob and enqueue it
    job = Printjob(username, newpath, num_pages)
    PRINTERTHREAD.enqueue(job)

    # create log message
    app.logger.info('Received print job from user %s with %s pages', username, num_pages)

    return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'],
                           num_documents=PRINTERTHREAD.get_queue_size(),
                           num_pages=PRINTERTHREAD.get_page_sum(),
                           success='Deine Datei wird nun verarbeitet. '
                                   + 'Bitte beachte, dass das Verarbeiten von großen '
                                   + 'PDFs unter Umständen mehrere Minuten dauern kann.')


# main printing page
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return handle_post()
    else:
        return handle_get()


# page for clearing the printer queue
@app.route('/printerqueue', methods=['GET', 'POST'])
def printerqueue():
    # handle different methods differently
    if request.method == 'GET':
        return render_template(
            'printerqueue.html',
            running=PRINTERTHREAD.is_alive(),
            numjobs=PRINTERTHREAD.get_queue_size(),
            numpages=PRINTERTHREAD.get_page_sum()
        )
    elif request.method == 'POST':
        # check if the password is correct
        if request.form['password'] != SECRETS['sftp_password']:
            return render_template(
                'printerqueue.html',
                running=PRINTERTHREAD.is_alive(),
                numjobs=PRINTERTHREAD.get_queue_size(),
                numpages=PRINTERTHREAD.get_page_sum(),
                error='Wrong password.')

        # clear the queue if the password was correct
        else:
            PRINTERTHREAD.clear_queue()
            return render_template(
                'printerqueue.html',
                numjobs=PRINTERTHREAD.get_queue_size(),
                numpages=PRINTERTHREAD.get_page_sum(),
                running=PRINTERTHREAD.is_alive(),
                success='Cleared queue.')
