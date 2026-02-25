from flask import Blueprint

bp = Blueprint('files', __name__, url_prefix='/api')

from app.files import routes
