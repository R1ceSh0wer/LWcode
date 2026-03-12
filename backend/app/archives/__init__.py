from flask import Blueprint

bp = Blueprint('archives', __name__, url_prefix='/api/archives')

from . import routes
