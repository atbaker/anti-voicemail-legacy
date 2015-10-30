from flask import Blueprint

voice = Blueprint('voice', __name__)

from . import views
