from flask import Blueprint

bp = Blueprint('comments', __name__, url_prefix='/api')

from app.comments import routes
