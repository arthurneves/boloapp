from flask_login import login_required, current_user
from . import main_bp, usuario_routes
from app.services.cache_service import cache_perfil_home


@main_bp.route('/')
@login_required
@cache_perfil_home()
def home():

    id_usuario = current_user.id_usuario

    return usuario_routes.perfil_usuario(id_usuario)
