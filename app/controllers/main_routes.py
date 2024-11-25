from flask import render_template
from flask_login import current_user
from app.models.promessa import Promessa
from app.models.transacao_pontos import TransacaoPontos
from app.models.usuario import Usuario
from . import main_bp

@main_bp.route('/')
def home():

    id_usuario = current_user.id_usuario

    usuario = Usuario.query.get_or_404(id_usuario)
    
    # Buscar promessas do usuário
    promessas = Promessa.query.filter_by(id_usuario=id_usuario).all()
    
    # Buscar transações de pontos do usuário
    transacoes = TransacaoPontos.query.filter_by(id_usuario=id_usuario).order_by(TransacaoPontos.data_criacao.desc()).all()
    
    # Buscar outros usuários da mesma squad
    usuarios_squad = []
    if usuario.squad:
        usuarios_squad = Usuario.query.filter(
            Usuario.id_squad == usuario.squad.id_squad, 
            Usuario.id_usuario != id_usuario
        ).all()
    
    return render_template('usuarios/perfil.html', 
                           usuario=usuario, 
                           promessas=promessas, 
                           transacoes=transacoes, 
                           usuarios_squad=usuarios_squad)
