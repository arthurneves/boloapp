from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.usuario import Usuario
from app.models.squad import Squad
from app.forms.usuario_forms import RegistroUsuarioForm, LoginForm, EdicaoUsuarioForm
from app.models.log import Log

usuario_bp = Blueprint('usuario', __name__)

@usuario_bp.route('/usuarios', methods=['GET'])
@login_required
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('usuarios/listar.html', usuarios=usuarios)

@usuario_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    form = RegistroUsuarioForm()
    if form.validate_on_submit():
        # Busca o squad selecionado
        squad = Squad.query.get(form.id_squad.data)
        novo_usuario = Usuario(
            nome_usuario=form.nome_usuario.data,
            email_usuario=form.email_usuario.data,
            is_ativo=form.is_ativo.data,
            is_administrador=form.is_administrador.data,
            squad=squad
        )
        novo_usuario.set_senha(form.senha.data)
        
        db.session.add(novo_usuario)
        db.session.commit()

        Log.criar_log(novo_usuario.id_usuario, 'usuario', 'criar')

        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('usuario.listar_usuarios'))
    return render_template('usuarios/novo.html', form=form)

@usuario_bp.route('/usuarios/editar/<int:id_usuario>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id_usuario):
    if not current_user.is_administrador:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
    
    usuario = Usuario.query.get_or_404(id_usuario)
    form = EdicaoUsuarioForm(usuario_id=id_usuario)
    
    if form.validate_on_submit():
        # Busca o squad selecionado
        squad = Squad.query.get(form.id_squad.data)
        
        usuario.nome_usuario = form.nome_usuario.data
        usuario.email_usuario = form.email_usuario.data
        usuario.is_ativo = form.is_ativo.data
        usuario.is_administrador = form.is_administrador.data
        usuario.squad = squad

        if form.senha.data:
            usuario.set_senha(form.senha.data)

        db.session.commit()

        Log.criar_log(id_usuario, 'usuario', 'editar')

        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('usuario.listar_usuarios'))
    
    if form.errors:
        return render_template('usuarios/editar.html', form=form, usuario=usuario)
    
    # Preenche o formulário com os dados atuais do usuário
    form.nome_usuario.data = usuario.nome_usuario
    form.email_usuario.data = usuario.email_usuario
    form.is_ativo.data = usuario.is_ativo
    form.is_administrador.data = usuario.is_administrador
    form.id_squad.data = usuario.id_squad if usuario.squad else 0
    
    return render_template('usuarios/editar.html', form=form, usuario=usuario)

@usuario_bp.route('/usuarios/desativar/<int:id_usuario>', methods=['GET'])
@login_required
def desativar_usuario(id_usuario):
    if not current_user.is_administrador:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
    
    usuario = Usuario.query.get_or_404(id_usuario)
    
    # Impede exclusão do próprio usuário
    if usuario.id_usuario == current_user.id_usuario:
        flash('Você não pode excluir seu próprio usuário', 'danger')
        return redirect(url_for('usuario.listar_usuarios'))
    
    usuario.is_ativo = False
    db.session.commit()

    Log.criar_log(id_usuario, 'usuario', 'desativar')

    flash('Usuário desativado com sucesso!', 'success')
    return redirect(url_for('usuario.listar_usuarios'))

@usuario_bp.route('/usuarios/reativar/<int:id_usuario>', methods=['GET'])
@login_required
def reativar_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    
    usuario.is_ativo = True
    db.session.commit()

    Log.criar_log(id_usuario, 'usuario', 'reativar')
    
    flash('Usuário reativado com sucesso!', 'success')
    return redirect(url_for('usuario.listar_usuarios'))

@usuario_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email_usuario=form.email_usuario.data).first()
        
        if usuario and usuario.check_senha(form.senha.data):
            if not usuario.is_ativo:
                flash('Usuário inativo. Entre em contato com o administrador.', 'warning')
                return redirect(url_for('main.login'))
            
            login_user(usuario)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.home'))
        
        flash('Email ou senha inválidos', 'danger')
    
    return render_template('usuarios/login.html', form=form)

@usuario_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('main.login'))
