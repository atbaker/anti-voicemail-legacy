from flask import Blueprint

setup = Blueprint('setup', __name__)

from . import views # flake8: noqa
