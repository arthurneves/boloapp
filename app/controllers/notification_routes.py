from flask import current_app, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.controllers import main_bp
from app.models.notification import Notification, NotificacaoEnviada, PublicoAlvo, StatusEnvio
from app.models.push_subscription import PushSubscription
from app.forms.notification_forms import NotificationForm, NotificationFilterForm
from app.services.notification_service import NotificationService, VAPID_KEYS
from datetime import datetime, timedelta
from sqlalchemy import desc
import json

@main_bp.route('/api/notificacoes/vapid-public-key', methods=['GET'])
def get_vapid_public_key():
    """
    Retorna a chave pública VAPID para ser usada pelo frontend
    """
    if not VAPID_KEYS:
        return jsonify({'error': 'Chaves VAPID não configuradas'}), 500
    
    return jsonify({
        'publicKey': VAPID_KEYS['public_key']
    })

@main_bp.route('/notificacoes', methods=['GET'])
@login_required
def listar_notificacoes():
    """
    Exibe a lista de notificações enviadas com opções de filtro
    """
    if not current_user.is_administrador:
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))
    
    form = NotificationFilterForm()
    
    # Aplicar filtros se fornecidos
    query = Notification.query
    
    if form.validate_on_submit():
        if form.data_inicio.data:
            query = query.filter(Notification.data_envio >= form.data_inicio.data)
        
        if form.data_fim.data:
            query = query.filter(Notification.data_envio <= form.data_fim.data)
        
        if form.status_envio.data:
            query = query.filter(Notification.status_envio == form.status_envio.data)
    
    # Configuração da paginação
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de itens por página
    
    # Ordenar por data de envio (mais recente primeiro) e paginar
    pagination = query.order_by(desc(Notification.data_envio)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    notificacoes = pagination.items
    
    return render_template('notifications/listar.html', 
                          notificacoes=notificacoes,
                          pagination=pagination,
                          form=form,
                          titulo="Histórico de Notificações")

@main_bp.route('/notificacoes/nova', methods=['GET', 'POST'])
@login_required
def nova_notificacao():
    """
    Exibe o formulário para criar uma nova notificação
    """
    if not current_user.is_administrador:
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))
    
    form = NotificationForm()
    
    if form.validate_on_submit():
        try:
            # Criar a notificação
            notificacao = NotificationService.criar_notificacao(
                titulo=form.titulo_notificacao.data,
                corpo=form.corpo_notificacao.data,
                publico_alvo=form.publico_alvo.data,
                id_usuario_criador=current_user.id_usuario,
                id_usuario_destino=form.id_usuario_destino.data if form.publico_alvo.data == PublicoAlvo.USUARIO_ESPECIFICO.value else None,
                id_squad_destino=form.id_squad_destino.data if form.publico_alvo.data == PublicoAlvo.SQUAD.value else None,
                agendamento=form.agendamento.data,
                is_ativo=form.is_ativo.data
            )
            
            flash('Notificação criada com sucesso!', 'success')
            return redirect(url_for('main.listar_notificacoes'))
        
        except Exception as e:
            flash(f'Erro ao criar notificação: {str(e)}', 'danger')
    
    return render_template('notifications/nova.html', 
                          form=form,
                          titulo="Nova Notificação")

@main_bp.route('/notificacoes/<int:id_notificacao>/editar', methods=['GET', 'POST'])
@login_required
def editar_notificacao(id_notificacao):
    """
    Exibe o formulário para editar uma notificação existente
    """
    if not current_user.is_administrador:
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))
    
    notificacao = Notification.query.get_or_404(id_notificacao)
    
    # Verificar se a notificação já foi enviada
    if notificacao.status_envio != StatusEnvio.PENDENTE.value:
        flash('Não é possível editar uma notificação que já foi enviada.', 'warning')
        return redirect(url_for('main.listar_notificacoes'))
    
    form = NotificationForm(obj=notificacao)
    
    if form.validate_on_submit():
        try:
            # Atualizar a notificação
            NotificationService.atualizar_notificacao(
                id_notificacao=id_notificacao,
                titulo=form.titulo_notificacao.data,
                corpo=form.corpo_notificacao.data,
                publico_alvo=form.publico_alvo.data,
                id_usuario_destino=form.id_usuario_destino.data if form.publico_alvo.data == PublicoAlvo.USUARIO_ESPECIFICO.value else None,
                id_squad_destino=form.id_squad_destino.data if form.publico_alvo.data == PublicoAlvo.SQUAD.value else None,
                agendamento=form.agendamento.data,
                is_ativo=form.is_ativo.data
            )
            
            flash('Notificação atualizada com sucesso!', 'success')
            return redirect(url_for('main.listar_notificacoes'))
        
        except Exception as e:
            flash(f'Erro ao atualizar notificação: {str(e)}', 'danger')
    
    return render_template('notifications/editar.html', 
                          form=form,
                          notificacao=notificacao,
                          titulo="Editar Notificação")

@main_bp.route('/notificacoes/<int:id_notificacao>/enviar', methods=['POST'])
@login_required
def enviar_notificacao(id_notificacao):
    """
    Envia uma notificação manualmente
    """
    logger = current_app.logger
    
    try:
        if not current_user.is_administrador:
            logger.warning(f"Tentativa de envio de notificação por usuário não administrador: {current_user.id_usuario}")
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('main.index'))
        
        # Verificar se a notificação existe
        notificacao = Notification.query.get_or_404(id_notificacao)
        logger.info(f"Iniciando envio manual da notificação {id_notificacao} por {current_user.id_usuario}")
        
        # Verificar estado da notificação
        if not notificacao.is_ativo:
            logger.warning(f"Tentativa de envio de notificação inativa: {id_notificacao}")
            flash('Não é possível enviar uma notificação inativa.', 'warning')
            return redirect(url_for('main.listar_notificacoes'))
        
        if notificacao.status_envio == StatusEnvio.ENVIADO.value:
            logger.warning(f"Tentativa de reenvio de notificação já enviada: {id_notificacao}")
            flash('Esta notificação já foi enviada.', 'warning')
            return redirect(url_for('main.listar_notificacoes'))
        
        # Enviar a notificação
        resultado = NotificationService.enviar_notificacao(id_notificacao)
        
        if resultado:
            logger.info(f"Notificação {id_notificacao} enviada com sucesso")
            flash('Notificação enviada com sucesso!', 'success')
        else:
            logger.warning(f"Não foi possível enviar a notificação {id_notificacao}")
            flash('Não foi possível enviar a notificação. Verifique o status e agendamento.', 'warning')
    
    except Exception as e:
        logger.error(f"Erro ao enviar notificação {id_notificacao}: {str(e)}", exc_info=True)
        flash(f'Erro ao enviar notificação: {str(e)}', 'danger')
    
    return redirect(url_for('main.listar_notificacoes'))

@main_bp.route('/notificacoes/<int:id_notificacao>/cancelar', methods=['POST'])
@login_required
def cancelar_notificacao(id_notificacao):
    """
    Cancela uma notificação pendente
    """
    if not current_user.is_administrador:
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))
    
    notificacao = Notification.query.get_or_404(id_notificacao)
    
    # Verificar se a notificação já foi enviada
    if notificacao.status_envio != StatusEnvio.PENDENTE.value:
        flash('Não é possível cancelar uma notificação que já foi enviada.', 'warning')
        return redirect(url_for('main.listar_notificacoes'))
    
    try:
        # Desativar a notificação
        notificacao.is_ativo = False
        db.session.commit()
        
        flash('Notificação cancelada com sucesso!', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cancelar notificação: {str(e)}', 'danger')
    
    return redirect(url_for('main.listar_notificacoes'))

@main_bp.route('/notificacoes/<int:id_notificacao>/detalhes', methods=['GET'])
@login_required
def detalhes_notificacao(id_notificacao):
    """
    Exibe os detalhes de uma notificação
    """
    if not current_user.is_administrador:
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))
    
    notificacao = Notification.query.get_or_404(id_notificacao)
    
    # Obter os destinatários que receberam a notificação
    destinatarios = []
    if notificacao.status_envio == StatusEnvio.ENVIADO.value:
        destinatarios = NotificacaoEnviada.query.\
            filter(NotificacaoEnviada.id_notificacao == id_notificacao).\
            all()
    
    return render_template('notifications/detalhes.html', 
                          notificacao=notificacao,
                          destinatarios=destinatarios,
                          titulo="Detalhes da Notificação")

@main_bp.route('/api/notificacoes/processar-agendadas', methods=['POST'])
def processar_notificacoes_agendadas():
    """
    Endpoint para processar notificações agendadas (chamado por um job agendado)
    """
    # Verificar token de autenticação (em um ambiente de produção, isso seria mais seguro)
    token = request.headers.get('Authorization')
    if not token or token != 'token-secreto-para-processar-notificacoes':
        abort(401)
    
    try:
        resultado = NotificationService.processar_notificacoes_agendadas()
        return jsonify({'success': resultado})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rotas para registro de dispositivos para notificações push (implementação futura)
from flask_wtf.csrf import generate_csrf
from functools import wraps

def ensure_json_response(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return decorated_function

from app import csrf
from flask_wtf.csrf import CSRFError

@main_bp.errorhandler(CSRFError)
def handle_csrf_error(e):
    return jsonify({
        'error': 'Token CSRF inválido',
        'csrf_token': generate_csrf()
    }), 400

@main_bp.route('/api/notificacoes/registrar-dispositivo', methods=['POST'])
@csrf.exempt
@ensure_json_response
def registrar_dispositivo():
    """
    Registra um dispositivo para receber notificações push
    """
    print("=== Início do processamento de registro de dispositivo ===")
    try:
        # Verificar autenticação
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Usuário não autenticado',
                'csrf_token': generate_csrf()
            }), 401

        # Log dos dados da requisição
        print("Headers:", dict(request.headers))
        data = request.get_json()
        if not data:
            print("Erro: Nenhum dado recebido no corpo da requisição")
            return jsonify({'error': 'Nenhum dado recebido'}), 400

        # Validar presença do campo subscription
        if 'subscription' not in data:
            print("Erro: Campo 'subscription' não encontrado nos dados", data.keys())
            return jsonify({'error': 'Dados de subscription são obrigatórios'}), 400

        subscription_data = data.get('subscription')
        print("Dados recebidos de subscription:", json.dumps(subscription_data, indent=2))

        # Validar estrutura dos dados
        if not isinstance(subscription_data, dict):
            print("Erro: Dados de subscription devem ser um objeto")
            return jsonify({'error': 'Dados de subscription inválidos'}), 400

        # Validar campos obrigatórios
        required_fields = ['endpoint', 'keys']
        for field in required_fields:
            if field not in subscription_data:
                print(f"Erro: Campo obrigatório '{field}' não encontrado")
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400

        # Validar campos da chave
        if not isinstance(subscription_data['keys'], dict):
            print("Erro: Campo 'keys' deve ser um objeto")
            return jsonify({'error': 'Formato inválido para o campo keys'}), 400

        if 'p256dh' not in subscription_data['keys'] or 'auth' not in subscription_data['keys']:
            print("Erro: Campos obrigatórios p256dh ou auth não encontrados em keys")
            return jsonify({'error': 'Campos p256dh e auth são obrigatórios'}), 400

        # Criar ou atualizar subscription
        print("Dados validados com sucesso, criando subscription...")
        try:
            subscription = PushSubscription.create_from_subscription(
                id_usuario=current_user.id_usuario,
                subscription_json=subscription_data
            )
            
            print("Subscription criada com sucesso:", {
                'id': subscription.id,
                'endpoint': subscription.endpoint[:50] + "...",
                'usuario_id': subscription.id_usuario
            })

            return jsonify({
                'success': True,
                'message': 'Dispositivo registrado com sucesso',
                'subscription_id': subscription.id
            })

        except Exception as e:
            print("Erro ao criar/atualizar subscription:", str(e))
            return jsonify({'error': 'Erro ao salvar registro do dispositivo'}), 500

    except Exception as e:
        print("Erro não esperado:", str(e))
        return jsonify({'error': 'Erro interno do servidor'}), 500

    finally:
        print("=== Fim do processamento de registro de dispositivo ===")
