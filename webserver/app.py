import os.path

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


def handle_get():
    return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'])


def handle_post():
    # get the uploaded file and validate filename
    uploaded_file = request.files['pdffile']
    secured_filename = secure_filename(uploaded_file.filename)

    # check extension
    if os.path.splitext(secured_filename)[1] != '.pdf':
        return render_template('index.html',
                               maxpdfsize=CONFIG['maxpdfsize'],
                               error='Sie können nur PDF Dateien drucken.')

    # check if file is really a pdf
    try:
        pdfreader = PdfFileReader(uploaded_file)
    except PdfReadError as error:
        return render_template('index.html',
                               maxpdfsize=CONFIG['maxpdfsize'],
                               error='Die PDF Datei kann nicht gelesen werden.')

    # check the number of pages
    if pdfreader.numPages > int(CONFIG['maxpdfsize']):
        return render_template('index.html',
                               maxpdfsize=CONFIG['maxpdfsize'],
                               error='Sie können nur PDFs mit maximal ' + CONFIG['maxpdfsize'] + ' Seitem drucken.')

    return handle_get()


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return handle_post()
    else:
        return handle_get()
