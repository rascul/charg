from os import environ
from os.path import exists

from flask import Flask
app = Flask(__name__)

import config
app.config.from_object(config)

import charg.views

