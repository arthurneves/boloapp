from flask_login import login_required, current_user
from . import main_bp, usuario_routes


@main_bp.route('/')
@login_required
def home():

    id_usuario = current_user.id_usuario

    return usuario_routes.perfil_usuario(id_usuario)

