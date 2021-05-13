from flask import Flask, render_template
import yaml
from yaml import YAMLError

app = Flask(__name__)

global CONFIG

@app.before_first_request
def setup():
    # try to load the config file
    with open('config.yml', 'r') as configfile:
        try:
            # load the config
            global CONFIG
            CONFIG = yaml.safe_load(configfile)
        except YAMLError as error:
            exit("Unable to load config: " + str(error))


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html', maxpdfsize=CONFIG['maxpdfsize'])
