from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
import models
import logging
from logging import handlers
import os

app: Flask = None
login_manager: LoginManager = None
mail: Mail = None
url: str = None


def init_app(config, url_):
    global app, login_manager, mail, url
    try:
        os.mkdir('log')
    except OSError:
        pass

    try:
        os.mkdir('db')
    except OSError:
        pass
    if url_ is None:
        url_ = 'localhost:5000'
    url = url_

    try:
        os.makedirs('libby/static/img')
    except Exception:
        pass

    app = Flask(__name__)
    app.config.from_object(config)

    login_manager = LoginManager(app)
    mail = Mail(app)

    app.logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)
    st = handlers.RotatingFileHandler('log/libby.log', backupCount=5, maxBytes=1024*1024)
    st.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)
    st.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(st)

    models.global_init(config.db_file)
    from libby import routes


def run(port=None, host=None):
    print(app.url_map)
    app.run(port=port, host=host)
