from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from app import cache, db
from datetime import datetime
from urllib.parse import urlencode
from . import main_bp
from app.models.log import Log
from app.models.promessa import Promessa
from app.models.usuario import Usuario
from app.forms.promessa_forms import PromessaForm
from app.services.cache_service import (
    make_cache_key_promessas,
    invalidar_cache_lista_promessa,
    invalidar_cache_perfil_usuario, 
    invalidar_cache_home
)
from app import db

@main_bp.route('/promessas', methods=['GET'])
@cache.cached(key_prefix=make_cache_key_promessas)
def listar_promessas():
    page = request.args.get('page', 1, type=int)
    titulo = request.args.get('titulo', '')
    status = request.args.get('status', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    usuario = request.args.get('usuario', '')

    # Construir query base
    query = Promessa.query

    # Aplicar filtros
    if titulo:
        query = query.filter(Promessa.titulo_promessa.ilike(f'%{titulo}%'))
    if status:
        if status == 'ativo':
            query = query.filter(Promessa.is_ativo == True)
        elif status == 'inativo':
            query = query.filter(Promessa.is_ativo == False)
    if data_inicio and data_fim:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%d/%m/%Y')
            data_fim_dt = datetime.strptime(data_fim, '%d/%m/%Y')
            query = query.filter(Promessa.data_criacao.between(data_inicio_dt, data_fim_dt))
        except ValueError:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                query = query.filter(Promessa.data_criacao.between(data_inicio_dt, data_fim_dt))
            except ValueError:
                pass
    if usuario:
        query = query.join(Usuario).filter(Usuario.nome_usuario.ilike(f'%{usuario}%'))

    # Ordenar e paginar
    paginated_promessas = query.order_by(Promessa.id_promessa.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template('promessas/listar.html',
                         promessas=paginated_promessas,
                         titulo=titulo,
                         status=status,
                         data_inicio=data_inicio,
                         data_fim=data_fim,
                         usuario=usuario)

@main_bp.route('/promessas/nova', methods=['GET', 'POST'])
@login_required
def criar_promessa():
    form = PromessaForm()
    
    if form.validate_on_submit():

        usuario = Usuario.query.get(form.id_usuario.data)

        nova_promessa = Promessa(
            titulo_promessa = form.titulo_promessa.data,
            descricao_promessa = form.descricao_promessa.data,
            is_ativo = True,
            id_usuario = usuario.id_usuario
        )
        
        db.session.add(nova_promessa)
        db.session.commit()

        # Invalidar todos os caches relacionados a promessas
        if not invalidar_cache_lista_promessa():
            current_app.logger.warning("Falha ao invalidar cache de lista de promessas")
        invalidar_cache_perfil_usuario(usuario.id_usuario)
        invalidar_cache_home(usuario.id_usuario)

        Log.criar_log(nova_promessa.id_promessa, 'promessa', 'criar', nova_promessa.id_usuario)
        
        flash('Promessa criada com sucesso!', 'success')
        return redirect(url_for('main.listar_promessas'))
    
    return render_template('promessas/nova.html', form=form)

@main_bp.route('/promessas/editar/<int:id_promessa>', methods=['GET', 'POST'])
@login_required
def editar_promessa(id_promessa):
    promessa = Promessa.query.get_or_404(id_promessa)
    
    form = PromessaForm(promessa_id=id_promessa)
    
    if form.validate_on_submit():

        usuario = Usuario.query.get(form.id_usuario.data)

        promessa.titulo_promessa = form.titulo_promessa.data
        promessa.descricao_promessa = form.descricao_promessa.data
        promessa.is_ativo = True
        promessa.id_usuario = usuario.id_usuario
        
        db.session.commit()

        # Invalidar todos os caches relacionados a promessas
        if not invalidar_cache_lista_promessa():
            current_app.logger.warning("Falha ao invalidar cache de lista de promessas")
        invalidar_cache_perfil_usuario(usuario.id_usuario)
        invalidar_cache_home(usuario.id_usuario)

        Log.criar_log(id_promessa, 'promessa', 'editar', promessa.id_usuario)
        
        flash('Promessa atualizada com sucesso!', 'success')
        return redirect(url_for('main.listar_promessas'))
    
    # Preenche o formulário com os dados existentes
    form.titulo_promessa.data = promessa.titulo_promessa
    form.descricao_promessa.data = promessa.descricao_promessa
    form.id_usuario.data = promessa.id_usuario if promessa.usuario else 0
    
    return render_template('promessas/editar.html', form=form, promessa=promessa)

@main_bp.route('/promessas/desativar/<int:id_promessa>', methods=['GET'])
@login_required
def desativar_promessa(id_promessa):
    promessa = Promessa.query.get_or_404(id_promessa)
    
    promessa.is_ativo = False
    db.session.commit()

    # Invalidar todos os caches relacionados a promessas
    if not invalidar_cache_lista_promessa():
        current_app.logger.warning("Falha ao invalidar cache de lista de promessas")
    invalidar_cache_perfil_usuario(promessa.usuario.id_usuario)
    invalidar_cache_home(promessa.usuario.id_usuario)

    Log.criar_log(id_promessa, 'promessa', 'desativar', promessa.id_usuario)
    
    flash('Promessa desativada com sucesso!', 'success')
    return redirect(url_for('main.listar_promessas'))

@main_bp.route('/promessas/reativar/<int:id_promessa>', methods=['GET'])
@login_required
def reativar_promessa(id_promessa):
    promessa = Promessa.query.get_or_404(id_promessa)

    promessa.is_ativo = True
    db.session.commit()

    # Invalidar todos os caches relacionados a promessas
    if not invalidar_cache_lista_promessa():
        current_app.logger.warning("Falha ao invalidar cache de lista de promessas")
    invalidar_cache_perfil_usuario(promessa.usuario.id_usuario)
    invalidar_cache_home(promessa.usuario.id_usuario)

    Log.criar_log(id_promessa, 'promessa', 'reativar', promessa.id_usuario)
    
    flash('Promessa reativada com sucesso!', 'success')
    return redirect(url_for('main.listar_promessas'))
