import os

from flask import Flask

from .main.routes import main
from .slack_bot.routes import slack_router
from .db.utils import db
from .errors.handlers import errors

SECRET_KEY = os.getenv('SECRET_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.register_blueprint(main)
app.register_blueprint(slack_router)
app.register_blueprint(errors)




