from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from datetime import datetime, timedelta
from app.models.log import Log
from app.models.squad import Squad
from app.models.convite import Convite
from app.forms.convite_forms import CriarConviteForm, CadastrarUsuarioConviteForm
from app.models.usuario import Usuario
from app.services.qrcode_service import QRcodeService
import secrets
from . import main_bp


def gerar_hash_convite():
    hash = secrets.token_urlsafe(4).replace('_', '').replace('-', '')[:6].upper()
    return hash[:3] + "-" + hash[3:]


@main_bp.route('/convites', methods=['GET', 'POST'])
@login_required
def criar_convite():
    if not current_user.is_administrador:
        flash('Você não tem permissão para criar convites.', 'danger')
        return redirect(url_for('main.home'))

    form = CriarConviteForm()
    if form.validate_on_submit():

        hash_conv = gerar_hash_convite()
        while Convite.query.filter_by(hash_convite=hash_conv).first():
            hash_conv = gerar_hash_convite()

        convite = Convite(hash_convite=hash_conv, id_usuario_responsavel=current_user.id_usuario)
        db.session.add(convite)
        db.session.flush()

        convite_url = url_for('main.cadastrar_usuario_convite', hash_convite=hash_conv, _external=True)

        qr_code_base64 = QRcodeService.gerar_qrcode(convite_url)

        Log.criar_log(convite.id_convite, 'convite', 'criar')
        db.session.commit()

        return render_template('convites/mostrar_convite.html', convite_url=convite_url, qr_code_base64=qr_code_base64)

    return render_template('convites/criar.html', form=form)

@main_bp.route('/convites/<hash_convite>', methods=['GET', 'POST'])
def cadastrar_usuario_convite(hash_convite):
    convite = Convite.query.filter_by(hash_convite=hash_convite, id_usuario_cadastrado=None, is_ativo=True).first_or_404()

    data_expiracao = convite.data_criacao + timedelta(days=7)
    if datetime.now() > data_expiracao:
        convite.is_ativo = False
        db.session.commit()

        flash('Este convite expirou pois foi criado há mais de 7 dias.', 'danger')

        return redirect(url_for('main.login'))
        
    form = CadastrarUsuarioConviteForm()

    if form.validate_on_submit():

        squad = Squad.query.get(form.id_squad.data)

        novo_usuario = Usuario(
            nome_usuario=form.nome_usuario.data,
            login_usuario=form.login_usuario.data,
            squad=squad
        )
        novo_usuario.set_senha(form.senha.data)

        db.session.add(novo_usuario)
        db.session.flush()

        convite.id_usuario_cadastrado = novo_usuario.id_usuario
        convite.data_usuario_cadastrado = db.func.now()
        
        db.session.add(convite)

        id_autor = current_user.id_usuario if current_user.is_authenticated else novo_usuario.id_usuario

        Log.criar_log(novo_usuario.id_usuario, 'usuario', 'criar-via-convite', novo_usuario.id_usuario, id_autor)
        db.session.commit()

        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('convites/cadastro.html', form=form, convite=convite)
