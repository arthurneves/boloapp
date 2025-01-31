from flask import render_template, redirect, request, url_for, flash
from flask_login import login_required
from app import db, cache
from datetime import datetime
from app.models.transacao_pontos import TransacaoPontos
from app.models.usuario import Usuario
from app.models.log import Log
from app.forms.transacao_pontos_forms import TransacaoPontosForm
from app.services.cache_service import (
    invalidar_cache_geral,
    make_cache_key_transacoes
)
from . import main_bp

@main_bp.route('/transacoes-pontos', methods=['GET'])
@login_required
@cache.cached(key_prefix=make_cache_key_transacoes)
def listar_transacoes_pontos():
    page = request.args.get('page', 1, type=int)
    descricao = request.args.get('descricao', '')
    status = request.args.get('status', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    usuario = request.args.get('usuario', '')
    categoria = request.args.get('categoria', type=int)

    # Construir query base
    query = TransacaoPontos.query

    # Consultar categorias ativas para o template
    from app.models.categoria import Categoria
    categorias_ativas = Categoria.query.filter_by(is_ativo=True).all()

    # Aplicar filtros
    if descricao:
        query = query.filter(TransacaoPontos.descricao_transacao.ilike(f'%{descricao}%'))
    if status:
        if status == 'ativo':
            query = query.filter(TransacaoPontos.is_ativo == True)
        elif status == 'inativo':
            query = query.filter(TransacaoPontos.is_ativo == False)
    if data_inicio and data_fim:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%d/%m/%Y')
            data_fim_dt = datetime.strptime(data_fim, '%d/%m/%Y')
            query = query.filter(TransacaoPontos.data_criacao.between(data_inicio_dt, data_fim_dt))
        except ValueError:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                query = query.filter(TransacaoPontos.data_criacao.between(data_inicio_dt, data_fim_dt))
            except ValueError:
                pass
    if usuario:
        query = query.join(Usuario).filter(Usuario.nome_usuario.ilike(f'%{usuario}%'))
    if categoria:
        query = query.filter(TransacaoPontos.id_categoria == categoria)

    # Ordenar e paginar
    paginated_transacoes = query.order_by(TransacaoPontos.id_transacao.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template('transacoes_pontos/listar.html',
                         transacoes=paginated_transacoes,
                         descricao=descricao,
                         status=status,
                         data_inicio=data_inicio,
                         data_fim=data_fim,
                         usuario=usuario,
                         categoria=categoria,
                         categorias_ativas=categorias_ativas)

@main_bp.route('/transacoes-pontos/nova', methods=['GET', 'POST'])
@login_required
def criar_transacao_pontos():

    id_usuario = request.args.get('id_usuario', default=None, type=int)

    form = TransacaoPontosForm(id_usuario=id_usuario)

    if form.validate_on_submit():
        nova_transacao = TransacaoPontos(
            id_usuario=form.id_usuario.data,
            id_categoria=form.id_categoria.data,
            pontos_transacao=form.pontos_transacao.data,
            descricao_transacao=form.descricao_transacao.data
        )
        
        db.session.add(nova_transacao)
        db.session.commit()

        invalidar_cache_geral()

        Log.criar_log(nova_transacao.id_transacao, 'transacao_bolos', 'criar', nova_transacao.id_usuario)

        if id_usuario:
            return redirect(url_for('main.perfil_usuario', id_usuario=id_usuario))
        

        flash('Transação de bolos criada com sucesso!', 'success')
        return redirect(url_for('main.listar_transacoes_pontos'))
    
    return render_template('transacoes_pontos/nova.html', form=form)

@main_bp.route('/transacoes-pontos/editar/<int:id_transacao>', methods=['GET', 'POST'])
@login_required
def editar_transacao_pontos(id_transacao):
    transacao = TransacaoPontos.query.get_or_404(id_transacao)
    form = TransacaoPontosForm()
    
    if form.validate_on_submit():

        transacao.aux_evento = 'edicao'

        if form.pontos_transacao.data < transacao.pontos_transacao:
            transacao.aux_saldo = form.pontos_transacao.data - transacao.pontos_transacao
        else:
            transacao.aux_saldo = transacao.pontos_transacao - form.pontos_transacao.data
 
        transacao.pontos_transacao = form.pontos_transacao.data

        transacao.id_usuario = form.id_usuario.data
        transacao.id_categoria = form.id_categoria.data
        transacao.descricao_transacao = form.descricao_transacao.data
        transacao.is_ativo = True  
     
        db.session.commit()

        invalidar_cache_geral()

        Log.criar_log(id_transacao, 'transacao_bolos', 'editar', transacao.id_usuario)
        
        flash('Transação de bolos atualizada com sucesso!', 'success')
        return redirect(url_for('main.listar_transacoes_pontos'))
    
    # Preenche o formulário com os dados atuais da transação
    form.id_usuario.data = transacao.id_usuario
    form.id_categoria.data = transacao.id_categoria
    form.pontos_transacao.data = transacao.pontos_transacao
    form.descricao_transacao.data = transacao.descricao_transacao
    
    return render_template('transacoes_pontos/editar.html', form=form, transacao=transacao)

@main_bp.route('/transacoes-pontos/desativar/<int:id_transacao>', methods=['GET'])
@login_required
def desativar_transacao_pontos(id_transacao):
    transacao = TransacaoPontos.query.get_or_404(id_transacao)

    transacao.aux_evento = 'desativacao'
    
    transacao.is_ativo = False
    db.session.commit()

    invalidar_cache_geral()

    Log.criar_log(id_transacao, 'transacao_bolos', 'desativar', transacao.id_usuario)
    
    flash('Transação de bolos desativada com sucesso!', 'success')
    return redirect(url_for('main.listar_transacoes_pontos'))

@main_bp.route('/transacoes-pontos/reativar/<int:id_transacao>', methods=['GET'])
@login_required
def reativar_transacao_pontos(id_transacao):
    transacao = TransacaoPontos.query.get_or_404(id_transacao)

    transacao.aux_evento = 'reativacao'
    
    transacao.is_ativo = True
    db.session.commit()

    invalidar_cache_geral()

    Log.criar_log(id_transacao, 'transacao_bolos', 'reativar', transacao.id_usuario)
    
    flash('Transação de bolos reativada com sucesso!', 'success')
    return redirect(url_for('main.listar_transacoes_pontos'))
