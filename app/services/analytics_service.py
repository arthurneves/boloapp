from datetime import datetime, timedelta
from sqlalchemy import distinct, func, desc
from app import cache, db
from app.models.transacao_pontos import TransacaoPontos
from app.models.usuario import Usuario
from app.models.promessa import Promessa, StatusPromessa

# Configurações padrão
DEFAULT_PERIOD_MONTHS = 6
CACHE_TIMEOUT = 3600  # 1 hora em segundos

def get_intervalo_de_datas(months=DEFAULT_PERIOD_MONTHS):
    """Retorna o intervalo de datas para análise"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months*30)  # aproximação de meses
    return start_date, end_date

@cache.memoize(timeout=CACHE_TIMEOUT)
def get_total_bolos():
    """Retorna o total de bolos (saldo) no sistema"""
    return db.session.query(func.sum(Usuario.saldo_pontos_usuario)).scalar() or 0

@cache.memoize(timeout=CACHE_TIMEOUT)
def get_total_usuarios():
    """Retorna o total de usuários ativos"""
    return Usuario.query.filter_by(is_ativo=True).count()

@cache.memoize(timeout=CACHE_TIMEOUT)
def get_total_squads():
    """Retorna o total de squads ativos"""
    return db.session.query(func.count(distinct(Usuario.id_squad))).filter(Usuario.id_squad.isnot(None)).scalar() or 0

@cache.memoize(timeout=CACHE_TIMEOUT)
def get_evolucao_transacoes(months=DEFAULT_PERIOD_MONTHS):
    """Retorna a evolução das transações de pontos agrupada por mês"""
    start_date, end_date = get_intervalo_de_datas(months)
    
    transacoes = db.session.query(
        func.date_format(TransacaoPontos.data_criacao, '%Y-%m').label('mes'),
        func.sum(TransacaoPontos.pontos_transacao).label('total'),
        func.sum(func.if_(TransacaoPontos.pontos_transacao > 0, TransacaoPontos.pontos_transacao, 0)).label('creditos'),
        func.sum(func.if_(TransacaoPontos.pontos_transacao < 0, TransacaoPontos.pontos_transacao, 0)).label('debitos')
    ).filter(
        TransacaoPontos.data_criacao.between(start_date, end_date),
        TransacaoPontos.is_ativo == True
    ).group_by('mes').order_by(desc('mes')).all()
    
    return [
        {
            'mes': transacao.mes,
            'total': transacao.total,
            'creditos': transacao.creditos,
            'debitos': abs(transacao.debitos) if transacao.debitos else 0
        }
        for transacao in transacoes
    ]


@cache.memoize(timeout=CACHE_TIMEOUT)
def get_promessas_status(months=DEFAULT_PERIOD_MONTHS):
    """Retorna a distribuição de status das promessas"""
    start_date, end_date = get_intervalo_de_datas(months)
    
    promessas = db.session.query(
        Promessa.status_promessa,
        func.count(Promessa.id_promessa).label('total')
    ).filter(
        Promessa.data_criacao.between(start_date, end_date)
    ).group_by(Promessa.status_promessa).all()
    
    status_map = {
        StatusPromessa.ATIVA: 'Ativas',
        StatusPromessa.INATIVA: 'Inativas',
        StatusPromessa.CUMPRIDA: 'Cumpridas'
    }
    
    return [
        {
            'status': status_map.get(status, 'Desconhecido'),
            'total': total
        }
        for status, total in promessas
    ]

@cache.memoize(timeout=CACHE_TIMEOUT)
def get_squad_bolos():
    """Retorna o total de bolos (saldo) por squad"""
    from app.models.squad import Squad
    return db.session.query(
        Usuario.id_squad,
        Squad.titulo_squad.label('nome_squad'),
        func.sum(Usuario.saldo_pontos_usuario).label('total_bolos')
    ).join(
        Squad, Squad.id_squad == Usuario.id_squad
    ).filter(
        Usuario.id_squad.isnot(None),
        Usuario.is_ativo == True
    ).group_by(Usuario.id_squad, Squad.titulo_squad).all()

def get_dashboard_data(months=DEFAULT_PERIOD_MONTHS):
    """Retorna todos os dados necessários para o dashboard"""
    return {
        'kpis': {
            'total_bolos': get_total_bolos(),
            'total_usuarios': get_total_usuarios(),
            'total_squads': get_total_squads()
        },
        'transacoes': get_evolucao_transacoes(months),
        'promessas': get_promessas_status(months),
        'squad_bolos': [
            {
                'id_squad': str(squad.id_squad),
                'nome_squad': squad.nome_squad,
                'total_bolos': squad.total_bolos
            }
            for squad in get_squad_bolos()
        ],
        'periodo': {
            'meses': months,
            'inicio': (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d'),
            'fim': datetime.now().strftime('%Y-%m-%d')
        }
    }
