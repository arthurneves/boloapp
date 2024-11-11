from sqlalchemy.exc import IntegrityError
from flask import flash, render_template, request, redirect, url_for, jsonify
from . import main_bp
from app.models.usuario import Usuario
from app import db

@main_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('usuarios/listar.html', usuarios=usuarios)

@main_bp.route('/usuarios/novo', methods=['GET', 'POST'])
def criar_usuario():

    if request.method == 'POST':
        dados = request.form

        novo_usuario = Usuario(
            nome_usuario=dados.get('nome_usuario'),
            email_usuario=dados.get('email_usuario'),
            is_ativo=bool(dados.get('is_ativo', False)),
            is_administrador=bool(dados.get('is_administrador', False))
        )

        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('main.listar_usuarios'))
        
        except IntegrityError:
            db.session.rollback()
            flash('Email já registrado.', 'danger')
            return render_template('usuarios/novo.html')

    return render_template('usuarios/novo.html')

@main_bp.route('/usuarios/editar/<int:id_usuario>', methods=['GET', 'POST'])
def editar_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)

    if request.method == 'POST':
        dados = request.form
        usuario.nome_usuario = dados.get('nome_usuario')
        usuario.email_usuario = dados.get('email_usuario')
        usuario.is_ativo = bool(dados.get('is_ativo'))
        usuario.is_administrador = bool(dados.get('is_administrador'))

        try:
            db.session.commit()
            flash('Usuário editado com sucesso!', 'success')

        except Exception as ex:
            flash('Falha na edição.', 'danger')
            return render_template('usuarios/editar.html', usuario=usuario)
            
        return redirect(url_for('main.listar_usuarios'))
    
    return render_template('usuarios/editar.html', usuario=usuario)

@main_bp.route('/usuarios/excluir/<int:id_usuario>', methods=['GET'])
def excluir_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    db.session.delete(usuario)
    db.session.commit()
    return redirect(url_for('main.listar_usuarios'))
