from flask import Blueprint

bp = Blueprint('neo4j', __name__, url_prefix='/api')

from app.neo4j import routes
