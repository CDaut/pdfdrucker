import os.path
import socket
from os.path import join
import time
from shutil import move

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from yaml import YAMLError, safe_load
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError

app = Flask(__name__)

global CONFIG


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


def validate_pdf(uploaded_file):
    secured_filename = secure_filename(uploaded_file.filename)

    if secured_filename == '':
        return 'Bitte laden sie eine Datei hoch.'

    # check extension
    if os.path.splitext(secured_filename)[1] != '.pdf':
        return 'Sie können nur PDF Dateien drucken.'

    # check if file is really a pdf
    try:
        pdfreader = PdfFileReader(uploaded_file)
    except PdfReadError:
        return 'Die PDF Datei kann nicht gelesen werden.'

    # check the number of pages
    if pdfreader.numPages > int(CONFIG['maxpdfsize']):
        return 'Sie können nur PDFs mit maximal ' + CONFIG['maxpdfsize'] + ' Seiten drucken.'

    return 'ISVALID'


def validate_user(formdata):
    username = formdata['username']
    password = formdata['password']

    if username == '' or password == '':
        return 'Ungültiger Nutzername und/oder ungültiges Passwort.'

    # TODO: Validate the user data against the DB

    return 'ISVALID'


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
    valid = validate_pdf(uploaded_file)

    if not valid == 'ISVALID':
        # remove file from tempdir
        os.remove(filename)

        return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'], error=valid)

    # at this point we know that the uploaded file is a valid pdf file

    # move uploaded pdffile to our print spooler
    spooler_dir = CONFIG['spooler_directory']
    newpath = join(spooler_dir, username + '_' + str(unixtime) + '.pdf')
    move(filename, newpath)

    # get cups server hostname
    hostname = socket.gethostbyname('cups')

    # call lp TODO: do not call lp here or dispatch thread ore something like that
    os.system('lp -h ' + hostname + ':631 -d ABH ' + newpath)

    return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'],
                           success='Ihre Datei wird nun in ihren persönlichen Druckaccount hochgeladen. '
                                   + 'Bitte beachten sie, dass das Verarbeiten von großen '
                                   + 'PDFs unter Umständen mehrere Minuten dauern kann.')


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return handle_post()
    else:
        return handle_get()
