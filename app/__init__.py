import os
from flask import Flask
from .db import db
from .auth import auth
from .rank import rank


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, template_folder="templates")

    # Config
    app.config.from_pyfile('config.py')

    # Initialize database and blueprint
    db.init_app(app)
    app.register_blueprint(auth)  # auth.py: auth = BluePrint(...)
    app.register_blueprint(rank)
    app.add_url_rule('/', endpoint='index')

    return app
