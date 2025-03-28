from flask import render_template, request
from flask_login import login_required

from . import main_bp
from app import cache
from app.models.log import Log
from app.forms.log_forms import LogFiltroForm
from app.services.cache_service import make_cache_key_logs
from sqlalchemy import desc


@main_bp.route('/logs', methods=['GET'])
@login_required
@cache.cached(key_prefix=make_cache_key_logs, timeout=600) # 10 minutos
def listar_logs():
    form = LogFiltroForm()
    
    # Configuração de paginação
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de logs por página

    # Configuração de ordenação
    sort_by = request.args.get('sort', 'data_criacao')
    sort_order = request.args.get('order', 'desc')

    # Construir query base
    query = Log.query

    # Aplicar filtros
    if form.validate_on_submit() or request.method == 'GET':
        # Filtro por usuário autor
        usuario_autor_id = request.args.get('usuario_autor', type=int, default=0)
        if usuario_autor_id and usuario_autor_id != 0:
            query = query.filter(Log.id_usuario_autor == usuario_autor_id)

        # Filtro por usuário afetado
        usuario_afetado_id = request.args.get('usuario_afetado', type=int, default=0)
        if usuario_afetado_id and usuario_afetado_id != 0:
            query = query.filter(Log.id_usuario_afetado == usuario_afetado_id)
        
        # Filtro por registro afetado
        registro_afetado_id = request.args.get('registro_afetado', type=int, default=0)
        if registro_afetado_id and registro_afetado_id != 0:
            query = query.filter(Log.id_registro_afetado == registro_afetado_id)
        
        # Filtro por tipo entidade
        tipo_entidade = request.args.get('tipo_entidade', type=str, default='')
        if tipo_entidade:
            query = query.filter(Log.tipo_entidade == tipo_entidade)

        # Filtro por ação
        acao = request.args.get('acao', type=str, default='')
        if acao:
            query = query.filter(Log.acao_log == acao)
        
        # Filtro por data
        data_inicio = request.args.get('data_inicio', type=str)
        data_fim = request.args.get('data_fim', type=str)
        if data_inicio:
            query = query.filter(Log.data_criacao >= data_inicio)
        if data_fim:
            query = query.filter(Log.data_criacao <= data_fim)

    # Aplicar ordenação
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(Log, sort_by))) if sort_by != '' else query
    else:
        query = query.order_by(getattr(Log, sort_by)) if sort_by != '' else query

    # Paginação
    logs_paginados = query.paginate(page=page, per_page=per_page, error_out=False)

    # Preencher o formulário com os valores dos filtros
    form.process(request.args)

    # Preparar dados para o template
    return render_template('logs/listar.html', 
                           logs=logs_paginados.items, 
                           form=form, 
                           pagination=logs_paginados,
                           sort_by=sort_by,
                           sort_order=sort_order)
