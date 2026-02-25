from flask import Blueprint

bp = Blueprint('conversations', __name__, url_prefix='/api')

from app.conversations import routes
