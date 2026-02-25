from flask import Blueprint

bp = Blueprint('students', __name__, url_prefix='/api')

from app.students import routes
