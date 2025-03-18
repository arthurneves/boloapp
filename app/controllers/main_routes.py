from flask import get_flashed_messages, jsonify, send_from_directory
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from . import main_bp, usuario_routes
from app.services.cache_service import cache_perfil_home


@main_bp.route('/')
@login_required
@cache_perfil_home()
def home():
    id_usuario = current_user.id_usuario

    return usuario_routes.perfil_usuario(id_usuario)


@main_bp.route('/api/csrf-token', methods=['GET'])
@login_required
def get_csrf_token():
    return jsonify({'csrf_token': generate_csrf()})


@main_bp.route('/service-worker.js')
def service_worker():
    response = send_from_directory('static/js', 'service-worker.js', mimetype='application/javascript')
    # Importante: Não fazer cache do service worker
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response

@main_bp.route("/api/mensagens")
def mensagens():
    mensagens = []
    for mensagem in get_flashed_messages():
        mensagens.append({"mensagem": mensagem})
    return jsonify(mensagens)
