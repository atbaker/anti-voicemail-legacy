from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy

from config import config
from .utils import convert_to_national_format

bootstrap = Bootstrap()
db = SQLAlchemy()


class SchemeProxyFix(object):
    """
    A small piece of WSGI middleware to tell Flask to use https when the
    X-Forwarded-Proto header is present (used by Heroku)
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        forwarded_scheme = environ.get('HTTP_X_FORWARDED_PROTO', '')
        if forwarded_scheme:
            environ['wsgi.url_scheme'] = forwarded_scheme
        return self.app(environ, start_response)


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Apply the SchemeProxyFix middleware
    app.wsgi_app = SchemeProxyFix(app.wsgi_app)

    bootstrap.init_app(app)
    db.init_app(app)

    from .setup import setup as setup_blueprint
    app.register_blueprint(setup_blueprint)

    from .voice import voice as voice_blueprint
    app.register_blueprint(voice_blueprint)

    # Register our custom template filter
    app.jinja_env.filters['national_format'] = convert_to_national_format

    return app
