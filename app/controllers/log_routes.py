from flask import Blueprint, render_template, request
from flask_login import login_required
from app import db
from app.models.log import Log
from app.models.usuario import Usuario
from app.forms.log_forms import LogFiltroForm
from sqlalchemy import desc

log_bp = Blueprint('log', __name__)

@log_bp.route('/logs', methods=['GET'])
@login_required
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
        query = query.order_by(desc(getattr(Log, sort_by)))
    else:
        query = query.order_by(getattr(Log, sort_by))

    # Paginação
    logs_paginados = query.paginate(page=page, per_page=per_page, error_out=False)

    # Preparar dados para o template
    return render_template('logs/listar.html', 
                           logs=logs_paginados.items, 
                           form=form, 
                           pagination=logs_paginados,
                           sort_by=sort_by,
                           sort_order=sort_order)
