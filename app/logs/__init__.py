from flask import Blueprint
logs_bp = Blueprint('logs', __name__, url_prefix='/logs')
from app.logs import routes