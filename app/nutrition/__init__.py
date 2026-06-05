from flask import Blueprint
nutrition_bp = Blueprint('nutrition', __name__, url_prefix='/nutrition')
from app.nutrition import routes