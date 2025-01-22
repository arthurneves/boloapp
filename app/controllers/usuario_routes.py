from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from wtforms.validators import ValidationError
from . import main_bp
from app.models.usuario import Usuario
from app.models.squad import Squad
from app.models.promessa import Promessa
from app.models.transacao_pontos import TransacaoPontos
from app.models.log import Log
from app.forms.usuario_forms import RegistroUsuarioForm, LoginForm, EdicaoUsuarioForm
from app.services.image_service import ImageService
from app import db
from app.services.cache_service import cache_perfil_usuario, invalidar_cache_perfil



@main_bp.route('/usuarios', methods=['GET'])
@login_required
def listar_usuarios():

    if not current_user.is_administrador:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))


    usuarios = Usuario.query.all()
    return render_template('usuarios/listar.html', usuarios=usuarios)

@main_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():

    if not current_user.is_administrador:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))

    form = RegistroUsuarioForm()
    if form.validate_on_submit():

        squad = Squad.query.get(form.id_squad.data)
        
        foto_perfil = None
        if form.foto_perfil.data:
            try:
                foto_upload = ImageService.save_profile_photo(form.foto_perfil.data)
                if foto_upload:
                    foto_perfil = foto_upload['original']
                    #foto_perfil_thumbnail = foto_upload['thumbnail']
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('usuarios/novo.html', form=form)
        
        novo_usuario = Usuario(
            nome_usuario=form.nome_usuario.data,
            login_usuario=form.login_usuario.data,
            is_ativo=form.is_ativo.data,
            is_administrador=form.is_administrador.data,
            squad=squad,
            foto_perfil=foto_perfil
        )
        novo_usuario.set_senha(form.senha.data)
        
        db.session.add(novo_usuario)
        db.session.commit()

        invalidar_cache_perfil()

        Log.criar_log(novo_usuario.id_usuario, 'usuario', 'criar', novo_usuario.id_usuario)

        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('main.listar_usuarios'))
    return render_template('usuarios/novo.html', form=form)

@main_bp.route('/usuarios/editar/<int:id_usuario>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id_usuario):
    if (not current_user.is_administrador) and (current_user.id_usuario != id_usuario):
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
    
    usuario = Usuario.query.get_or_404(id_usuario)
    form = EdicaoUsuarioForm(usuario_id=id_usuario)
    
    if form.validate_on_submit():

        # Validar senha se estiver preenchido
        if form.senha.data:
            try:
                form.validate_edicao_senha(form.senha.data, form.confirmar_senha.data)
            except ValidationError as e:
                flash(str(e), 'danger')
                return render_template('usuarios/editar.html', form=form, usuario=usuario)

        squad = Squad.query.get(form.id_squad.data)
        
        if form.foto_perfil.data:
            try:
                # Deleta existente
                if usuario.foto_perfil:
                    ImageService.delete_profile_photo(usuario.foto_perfil)
                
                # Salva
                foto_upload = ImageService.save_profile_photo(form.foto_perfil.data)
                usuario.foto_perfil = foto_upload['original']
                #usuario.foto_perfil_thumbnail = foto_upload['thumbnail']
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('usuarios/editar.html', form=form, usuario=usuario)

        usuario.nome_usuario = form.nome_usuario.data
        usuario.login_usuario = form.login_usuario.data
        usuario.is_ativo = form.is_ativo.data
        usuario.is_administrador = form.is_administrador.data
        usuario.squad = squad

        if form.senha.data:
            usuario.set_senha(form.senha.data)

        db.session.commit()

        invalidar_cache_perfil()

        Log.criar_log(id_usuario, 'usuario', 'editar', id_usuario)

        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('main.listar_usuarios'))
    
    if form.errors:
        return render_template('usuarios/editar.html', form=form, usuario=usuario)
    
    # Preenche o formulário com os dados atuais do usuário
    form.nome_usuario.data = usuario.nome_usuario
    form.login_usuario.data = usuario.login_usuario
    form.is_ativo.data = usuario.is_ativo
    form.is_administrador.data = usuario.is_administrador
    form.id_squad.data = usuario.id_squad if usuario.squad else 0
    
    return render_template('usuarios/editar.html', form=form, usuario=usuario)

@main_bp.route('/usuarios/desativar/<int:id_usuario>', methods=['GET'])
@login_required
def desativar_usuario(id_usuario):
    if not current_user.is_administrador:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
    
    usuario = Usuario.query.get_or_404(id_usuario)
    
    # Impede exclusão do próprio usuário
    if usuario.id_usuario == current_user.id_usuario:
        flash('Você não pode desativar seu próprio usuário', 'danger')
        return redirect(url_for('main.listar_usuarios'))
    
    usuario.is_ativo = False
    db.session.commit()

    Log.criar_log(id_usuario, 'usuario', 'desativar', id_usuario)

    flash('Usuário desativado com sucesso!', 'success')
    return redirect(url_for('main.listar_usuarios'))

@main_bp.route('/usuarios/reativar/<int:id_usuario>', methods=['GET'])
@login_required
def reativar_usuario(id_usuario):

    if not current_user.is_administrador:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))

    usuario = Usuario.query.get_or_404(id_usuario)
    
    usuario.is_ativo = True
    db.session.commit()

    Log.criar_log(id_usuario, 'usuario', 'reativar', id_usuario)
    
    flash('Usuário reativado com sucesso!', 'success')
    return redirect(url_for('main.listar_usuarios'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(login_usuario=form.login_usuario.data).first()
        
        if usuario and usuario.check_senha(form.senha.data):
            if not usuario.is_ativo:
                flash('Usuário inativo. Entre em contato com o administrador.', 'warning')
                return redirect(url_for('main.login'))
            
            login_user(usuario)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.home'))
        
        flash('Login ou senha inválidos', 'danger')
    
    return render_template('usuarios/login.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('main.login'))

@main_bp.route('/perfil/<int:id_usuario>', methods=['GET'])
@login_required
@cache_perfil_usuario()
def perfil_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    
    # Buscar promessas do usuário
    promessas = Promessa.query.filter_by(
        id_usuario=id_usuario, 
        is_ativo=1
    ).order_by(Promessa.data_criacao.desc()).limit(5).all()
    
    # Buscar transações de pontos do usuário
    transacoes = TransacaoPontos.query.filter_by(
        id_usuario=id_usuario, 
        is_ativo=1
    ).order_by(TransacaoPontos.data_criacao.desc()).limit(5).all()
    
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
