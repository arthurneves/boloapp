from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.log import Log
from app.models.squad import Squad
from app.models.convite import Convite
from app.forms.convite_forms import CriarConviteForm, CadastrarUsuarioConviteForm
from app.models.usuario import Usuario
import secrets
import qrcode
from io import BytesIO
from base64 import b64encode
from . import main_bp

def gerar_hash_convite():
    hash = secrets.token_urlsafe(4).replace('_', '').replace('-', '')[:6].upper()
    return hash[:3] + "-" + hash[3:]


@main_bp.route('/convites', methods=['GET', 'POST'])
@login_required
def criar_convite():
    if not current_user.is_administrador:
        flash('Você não tem permissão para criar convites.', 'danger')
        return redirect(url_for('main.index'))

    form = CriarConviteForm()
    if form.validate_on_submit():
        hash_conv = gerar_hash_convite()
        while Convite.query.filter_by(hash_convite=hash_conv).first():
            hash_conv = gerar_hash_convite()

        convite = Convite(hash_convite=hash_conv, id_usuario_responsavel=current_user.id_usuario)
        db.session.add(convite)
        db.session.commit()

        convite_url = url_for('main.cadastrar_usuario_convite', hash_convite=hash_conv, _external=True)

        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
        )
        qr.add_data(convite_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        qr_code_base64 = b64encode(img_io.read()).decode('utf-8')

        Log.criar_log(convite.id_convite, 'convite', 'criar')

        return render_template('convites/mostrar_convite.html', convite_url=convite_url, qr_code_base64=qr_code_base64)

    return render_template('convites/criar.html', form=form)

@main_bp.route('/convites/<hash_convite>', methods=['GET', 'POST'])
def cadastrar_usuario_convite(hash_convite):
    convite = Convite.query.filter_by(hash_convite=hash_convite, id_usuario_cadastrado=None, is_ativo=True).first_or_404()
    form = CadastrarUsuarioConviteForm()
    if form.validate_on_submit():

        # Busca o squad selecionado
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
        db.session.commit()

        id_autor = current_user.id_usuario if current_user.is_authenticated else novo_usuario.id_usuario

        Log.criar_log(novo_usuario.id_usuario, 'usuario', 'criar-via-convite', novo_usuario.id_usuario, id_autor)

        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('convites/cadastro.html', form=form, convite=convite)
