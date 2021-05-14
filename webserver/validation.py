import os

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError
from werkzeug.utils import secure_filename


def validate_pdf(uploaded_file, CONFIG):
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
