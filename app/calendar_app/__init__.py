import os

from flask import Flask

from .logic.routes import main
from .db.utils import db
from .errors.handlers import errors

SECRET_KEY = os.getenv('SECRET_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.register_blueprint(main)
app.register_blueprint(errors)
