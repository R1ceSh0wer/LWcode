from flask import Blueprint

bp = Blueprint('columns', __name__, url_prefix='/api')

from app.columns import routes
