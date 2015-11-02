from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from config import config

from .utils import convert_to_national_format

bootstrap = Bootstrap()
mail = Mail()
db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    db.init_app(app)

    from .setup import setup as setup_blueprint
    app.register_blueprint(setup_blueprint)

    from .voice import voice as voice_blueprint
    app.register_blueprint(voice_blueprint)

    # Register our custom template filter
    app.jinja_env.filters['national_format'] = convert_to_national_format

    return app
