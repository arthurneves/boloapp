from flask import render_template
from flask_login import login_required, current_user
from app.models.promessa import Promessa
from app.models.transacao_pontos import TransacaoPontos
from app.models.usuario import Usuario
import secrets
from . import main_bp

def gerar_hash_convite():
    hash = secrets.token_urlsafe(4).replace('_', '').replace('-', '')[:6].upper()
    return hash[:3] + "-" + hash[3:]

@main_bp.route('/')
@login_required
def home():

    id_usuario = current_user.id_usuario

    usuario = Usuario.query.get_or_404(id_usuario)

    # Buscar promessas do usuário
    promessas = Promessa.query.filter_by(id_usuario=id_usuario, is_ativo=1).order_by(Promessa.data_criacao.desc()).limit(5).all()

    # Buscar transações de pontos do usuário
    transacoes = TransacaoPontos.query.filter_by(id_usuario=id_usuario, is_ativo=1).order_by(TransacaoPontos.data_criacao.desc()).limit(5).all()

    # Buscar outros usuários da mesma squad
    usuarios_squad = []
    if usuario.squad:
        usuarios_squad = Usuario.query.filter(
            Usuario.id_squad == usuario.squad.id_squad
        ).all()

    return render_template('usuarios/perfil.html',
                           usuario=usuario,
                           promessas=promessas,
                           transacoes=transacoes,
                           usuarios_squad=usuarios_squad)
