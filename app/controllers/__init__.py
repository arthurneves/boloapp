from flask import Blueprint

main_bp = Blueprint('main', __name__)

from . import main_routes
from . import usuario_routes
from . import squad_routes
from . import categoria_routes
from . import transacao_pontos_routes
from . import promessa_routes
from . import log_routes
from . import convite_routes
