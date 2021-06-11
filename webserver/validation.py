import os
import hashlib

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError
from werkzeug.utils import secure_filename
from mysql.connector import connect


def validate_pdf(uploaded_file, CONFIG):
    secured_filename = secure_filename(uploaded_file.filename)

    if secured_filename == '':
        return 'Bitte lad eine Datei hoch.'

    # check extension
    if os.path.splitext(secured_filename)[1] != '.pdf':
        return 'Du kannst nur PDF Dateien drucken.'

    # check if file is really a pdf
    try:
        pdfreader = PdfFileReader(uploaded_file)
    except PdfReadError:
        return 'Die PDF Datei kann nicht gelesen werden.'

    # avoid the "NotImplementedError" by trying to get the page count
    try:
        numpages = pdfreader.numPages
    except PdfReadError:
        return 'Die Seitenzahl konnte nicht ermittelt werden (ist die Datei vielleicht verschlüsselt?).'

    # check the number of pages
    if numpages > int(CONFIG['maxpdfsize']):
        return 'Du kannst nur PDFs mit maximal ' + CONFIG['maxpdfsize'] + ' Seiten drucken.'

    return 'ISVALID'


def get_number_of_pages(pdffile):
    return PdfFileReader(pdffile).numPages


def validate_user(formdata, CONFIG, secrets):
    username = formdata['username']
    password = formdata['password']

    if username == '' or password == '':
        return 'Ungültiger Nutzername und/oder ungültiges Passwort.'

    # connect to the SQL database
    db_connection = connect(
        host=CONFIG['db_address'],
        user=secrets['username'],
        password=secrets['db_password'],
        database=CONFIG['db_name']
    )
    cursor = db_connection.cursor()

    #  build and run SQL query
    query = "SELECT pass_md5" \
            " FROM logins" \
            " WHERE username ='" + username + "'"

    cursor.execute(query)
    # get the result
    result = cursor.fetchall()

    # check if the user was found
    if len(result) == 0:
        return 'Unbekannter Benutzer oder ungültiges Passwort.'

    # the passwords in the db are hashed using the md5() function in php
    # hash the submitted password and check it against the db
    hasher = hashlib.md5()
    hasher.update(password.encode())
    hashed_password = hasher.hexdigest()

    hash_from_db = result[0][0]

    if hashed_password != hash_from_db:
        return 'Unbekannter Benutzer oder ungültiges Passwort.'

    return 'ISVALID'
