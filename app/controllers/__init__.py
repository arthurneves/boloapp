from flask import Blueprint

main_bp = Blueprint('main', __name__)

from . import main_routes
from . import usuario_routes
from . import squad_routes
