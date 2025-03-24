from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
import json
import logging
from pywebpush import webpush, WebPushException
from app import db
from app.models.notification import NotificacaoEnviada, Notification, PublicoAlvo, StatusEnvio
from app.models.push_subscription import PushSubscription
import os
from concurrent.futures import ThreadPoolExecutor
from flask import current_app
import threading
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models.usuario import Usuario
from app.utils.db_session import get_scoped_session
from typing import List
from urllib.parse import urlparse
import time
import copy

logger = logging.getLogger(__name__)

def execute_with_app_context(app, func, *args, **kwargs):
    """
    Executa uma função com um novo contexto da aplicação para garantir 
    isolamento e consistência na thread
    """
    try:
        # Criar novo contexto para esta execução específica
        with app.app_context():
            return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Erro ao executar função com app context: {str(e)}", exc_info=True)
        raise

def create_vapid_claims(endpoint, expiration=12 * 3600):
    """Cria claims VAPID para um endpoint específico"""
    try:
        endpoint_url = urlparse(endpoint)
        base_url = f"{endpoint_url.scheme}://{endpoint_url.netloc}"
        
        claims = {
            "sub": f"mailto:{os.getenv('VAPID_CLAIM_EMAIL', 'admin@example.com')}",
            "aud": base_url,
            "exp": int(time.time()) + expiration
        }
        logger.debug(f"Claims VAPID gerados: {claims}")
        return claims
    except Exception as e:
        logger.error(f"Erro ao criar claims VAPID: {str(e)}")
        raise

def _load_vapid_keys():
    """Carrega e valida as chaves VAPID"""
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    import base64

    private_key_b64 = os.getenv('VAPID_PRIVATE_KEY')
    public_key_b64 = os.getenv('VAPID_PUBLIC_KEY')
    claim_email = os.getenv('VAPID_CLAIM_EMAIL', 'admin@example.com')

    if not private_key_b64 or not public_key_b64:
        logger.error("Chaves VAPID não encontradas!")
        raise ValueError("Chaves VAPID não configuradas no .env")

    try:
        # Processamento das chaves (mantido o código existente)
        private_key = private_key_b64.strip()
        private_key = private_key.replace('-----BEGIN PRIVATE KEY-----', '')
        private_key = private_key.replace('-----END PRIVATE KEY-----', '')
        private_key = private_key.replace('\n', '').strip()
        
        public_key = public_key_b64.strip()
        if public_key.startswith('-----BEGIN PUBLIC KEY-----'):
            public_key = public_key.replace('-----BEGIN PUBLIC KEY-----', '')
            public_key = public_key.replace('-----END PUBLIC KEY-----', '')
            public_key = public_key.replace('\n', '').strip()
        
        private_key = private_key.replace('+', '-').replace('/', '_')
        public_key = public_key.replace('+', '-').replace('/', '_')
        
        return {
            'private_key': private_key,
            'public_key': public_key
        }
    except Exception as e:
        logger.error(f"Erro ao processar chaves VAPID: {str(e)}")
        raise ValueError(f"Erro ao processar chaves VAPID: {str(e)}")

try:
    VAPID_KEYS = _load_vapid_keys()
except Exception as e:
    logger.error(f"Erro ao carregar chaves VAPID: {str(e)}")
    VAPID_KEYS = None

class NotificationService:
    _executor = ThreadPoolExecutor(max_workers=5)
    _app = None
    _max_retries = 3
    _retry_delay = 1

    @classmethod
    def init_app(cls, app):
        """Initialize with Flask app instance"""
        cls._app = app

    @classmethod
    def get_vapid_public_key(cls):
        """Retorna a chave pública VAPID para uso no frontend"""
        if VAPID_KEYS:
            return VAPID_KEYS['public_key']
        return None

    @classmethod
    def criar_notificacao(cls, titulo, corpo, publico_alvo, id_usuario_criador, 
                         id_usuario_destino=None, id_squad_destino=None, 
                         agendamento=None, is_ativo=True):
        """
        Cria uma nova notificação no sistema.
        
        Retorna o objeto notificação criado e persistido.
        Em caso de erro, lança uma exceção que deve ser tratada pelo chamador.
        """
        if not cls._app:
            raise RuntimeError("NotificationService não foi inicializado com init_app()")

        logger.info(f"Iniciando criação de notificação: titulo='{titulo}', publico_alvo={publico_alvo}")
        
        try:
            # Criar objeto notificação
            notificacao = Notification(
                titulo_notificacao=titulo,
                corpo_notificacao=corpo,
                publico_alvo=publico_alvo,
                id_usuario_criador=id_usuario_criador,
                id_usuario_destino=id_usuario_destino,
                id_squad_destino=id_squad_destino,
                agendamento=agendamento,
                is_ativo=is_ativo,
                status_envio=StatusEnvio.PENDENTE.value
            )
            
            # Adicionar à sessão e obter ID
            db.session.add(notificacao)
            db.session.flush()
            
            logger.info(f"Notificação {notificacao.id_notificacao} criada com sucesso")
            
            # Commitar transação para garantir que a notificação está persistida
            db.session.commit()
            
            logger.info(f"Notificação {notificacao.id_notificacao} persistida com sucesso")
            
            # Se não houver agendamento e estiver ativa, disparar envio assíncrono
            if not agendamento and is_ativo:
                logger.info(f"Iniciando envio assíncrono da notificação {notificacao.id_notificacao}")
                future = cls._executor.submit(
                    execute_with_app_context,
                    cls._app,
                    cls._enviar_notificacao_impl,
                    notificacao.id_notificacao
                )
                future.add_done_callback(lambda f: logger.info(
                    f"Envio assíncrono da notificação {notificacao.id_notificacao} concluído com status: {'Sucesso' if not f.exception() else 'Falha'}"
                ))

            return notificacao

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar notificação: {str(e)}")
            raise ValueError(f"Erro ao criar notificação: {str(e)}")

    @classmethod
    def enviar_notificacao(cls, id_notificacao):
        """Envia uma notificação de forma assíncrona."""
        if not cls._app:
            raise RuntimeError("NotificationService não foi inicializado com init_app()")

        try:
            logger.info(f"Iniciando envio da notificação {id_notificacao}")

            with get_scoped_session() as session:
                notificacao = session.query(Notification).get(id_notificacao)
                if not notificacao:
                    logger.error(f"Notificação {id_notificacao} não encontrada")
                    return False

                if not notificacao.is_ativo or notificacao.status_envio == StatusEnvio.ENVIADO.value:
                    return False

                notificacao.status_envio = StatusEnvio.PROCESSANDO.value
                session.commit()

            # Executar envio em thread com novo contexto
            future = cls._executor.submit(
                execute_with_app_context,
                cls._app,
                cls._enviar_notificacao_impl,
                id_notificacao
            )

            # Aguardar resultado com timeout
            result = future.result(timeout=60)  # Aumentado para 60 segundos
            logger.info(f"Resultado do envio da notificação {id_notificacao}: {'Sucesso' if result else 'Falha'}")
            return result

        except Exception as e:
            logger.error(f"Erro ao processar envio da notificação {id_notificacao}: {str(e)}", exc_info=True)
            with get_scoped_session() as session:
                notificacao = session.query(Notification).get(id_notificacao)
                if notificacao:
                    notificacao.status_envio = StatusEnvio.FALHA.value
                    session.commit()
            return False

    @classmethod
    def _enviar_notificacao_impl(cls, id_notificacao):
        """Implementação do envio de notificação"""
        thread_id = threading.get_ident()
        start_time = time.time()
        logger.info(f"Thread {thread_id}: Iniciando envio da notificação {id_notificacao}")

        with get_scoped_session() as session:
            try:
                notificacao = session.query(Notification).get(id_notificacao)
                if not notificacao or not notificacao.is_ativo:
                    return False

                # Obter IDs dos destinatários
                destinatarios_ids = cls._obter_destinatarios(session, notificacao)
                destinatarios_filtrados = [
                    id_usuario for id_usuario in destinatarios_ids
                    if NotificacaoEnviada.get_notificacoes_enviadas_hoje(id_usuario) < 300
                ]

                logger.info(
                    f"Thread {thread_id}: Processando {len(destinatarios_filtrados)} destinatários "
                    f"de um total de {len(destinatarios_ids)} encontrados"
                )

                envios_bem_sucedidos = 0
                envios_com_erro = 0

                # Enviar para cada destinatário
                for id_usuario in destinatarios_filtrados:
                    try:
                        result = cls._enviar_para_usuario(
                            id_notificacao,
                            id_usuario,
                            notificacao.titulo_notificacao,
                            notificacao.corpo_notificacao
                        )
                        if result:
                            envios_bem_sucedidos += 1
                        else:
                            envios_com_erro += 1
                    except Exception as e:
                        logger.error(f"Thread {thread_id}: Erro ao enviar para usuário {id_usuario}: {str(e)}")
                        envios_com_erro += 1

                # Atualizar status final
                with get_scoped_session() as final_session:
                    notificacao = final_session.query(Notification).get(id_notificacao)
                    if notificacao:
                        if envios_bem_sucedidos > 0:
                            notificacao.status_envio = StatusEnvio.ENVIADO.value if envios_com_erro == 0 \
                                else StatusEnvio.ENVIADO_PARCIAL.value
                        else:
                            notificacao.status_envio = StatusEnvio.FALHA.value

                        notificacao.data_envio = datetime.now()
                        notificacao.total_enviados = envios_bem_sucedidos
                        notificacao.total_falhas = envios_com_erro
                        final_session.commit()

                execution_time = time.time() - start_time
                logger.info(
                    f"Thread {thread_id}: Notificação {id_notificacao} processada em {execution_time:.2f}s "
                    f"(Sucesso: {envios_bem_sucedidos}, Falhas: {envios_com_erro})"
                )
                return envios_bem_sucedidos > 0

            except Exception as e:
                logger.error(
                    f"Thread {thread_id}: Erro ao processar notificação {id_notificacao}: {str(e)}",
                    exc_info=True
                )
                with get_scoped_session() as error_session:
                    notificacao = error_session.query(Notification).get(id_notificacao)
                    if notificacao:
                        notificacao.status_envio = StatusEnvio.FALHA.value
                        error_session.commit()
                return False

    @classmethod
    def _enviar_para_usuario(cls, id_notificacao, id_usuario, titulo, corpo):
        """Envia notificação para um usuário específico"""
        thread_id = threading.get_ident()
        logger.info(f"Thread {thread_id}: Enviando notificação {id_notificacao} para usuário {id_usuario}")
        
        with get_scoped_session() as session:
            try:
                # Verificar duplicação
                if session.query(NotificacaoEnviada).filter_by(
                    id_notificacao=id_notificacao,
                    id_usuario=id_usuario
                ).first():
                    return True

                # Preparar dados
                notification_data = {
                    "title": titulo,
                    "body": corpo,
                    "url": f"/notificacoes/{id_notificacao}/detalhes"
                }
                
                # Buscar subscrições
                subscriptions = session.query(PushSubscription).filter_by(
                    id_usuario=id_usuario,
                    is_ativo=True
                ).all()
                
                if not subscriptions:
                    return False
                
                envios_sucesso = 0
                for subscription in subscriptions:
                    try:
                        push_data = subscription.to_web_push_data()
                        if not push_data or not push_data.get('endpoint'):
                            continue

                        if cls._enviar_push_notification(push_data, notification_data):
                            notificacao_enviada = NotificacaoEnviada(
                                id_notificacao=id_notificacao,
                                id_usuario=id_usuario
                            )
                            session.add(notificacao_enviada)
                            envios_sucesso += 1
                            break
                    except WebPushException as e:
                        if hasattr(e, 'response') and e.response.status_code == 410:
                            subscription.is_ativo = False
                            session.flush()
                
                if envios_sucesso > 0:
                    session.commit()
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Thread {thread_id}: Erro ao processar usuário {id_usuario}: {str(e)}")
                session.rollback()
                return False

    @classmethod
    @retry(
        stop=stop_after_attempt(5),  # Aumentado para 5 tentativas
        wait=wait_exponential(multiplier=1, min=4, max=30),  # Máximo de espera aumentado para 30s
        retry_error_cls=(WebPushException, ConnectionError)  # Especificar quais erros devem causar retry
    )
    def _enviar_push_notification(cls, subscription_data, notification_data):
        """Envia uma notificação push com retry automático"""
        if not VAPID_KEYS:
            raise ValueError("Chaves VAPID não configuradas")
        
        # Gerar claims específicos para o endpoint
        vapid_claims = create_vapid_claims(subscription_data['endpoint'])
        
        response = webpush(
            subscription_info=subscription_data,
            data=json.dumps(notification_data),
            vapid_private_key=VAPID_KEYS['private_key'],
            vapid_claims=vapid_claims
        )
        
        return True

    @staticmethod
    def _obter_destinatarios(session, notificacao) -> List[int]:
        """Obtém a lista de IDs dos usuários destinatários"""
        logger.info(f"_obter_destinatarios chamado para notificação {notificacao.id_notificacao}")
        if notificacao.publico_alvo == PublicoAlvo.TODOS.value:
            return [
                id for (id,) in 
                session.query(Usuario.id_usuario).filter_by(is_ativo=True).all()
            ]
        
        elif notificacao.publico_alvo == PublicoAlvo.USUARIO_ESPECIFICO.value:
            if not notificacao.id_usuario_destino:
                return []
            
            exists = session.query(Usuario.id_usuario).filter_by(
                id_usuario=notificacao.id_usuario_destino,
                is_ativo=True
            ).scalar() is not None
            
            return [notificacao.id_usuario_destino] if exists else []
        
        elif notificacao.publico_alvo == PublicoAlvo.SQUAD.value:
            if not notificacao.id_squad_destino:
                return []
            
            return [
                id for (id,) in
                session.query(Usuario.id_usuario).filter_by(
                    id_squad=notificacao.id_squad_destino,
                    is_ativo=True
                ).all()
            ]
        
        return []

    @classmethod
    def shutdown(cls):
        """Encerra o executor de threads de forma limpa"""
        logger.info("Encerrando NotificationService executors...")
        if cls._executor:
            cls._executor.shutdown(wait=True)
        logger.info("NotificationService executors encerrados com sucesso")

    @classmethod
    def send_push_notification(cls, notification_type, entity, action):
        """
        Envia uma notificação push para os usuários relevantes com base no tipo de notificação, entidade e ação.
        """

        logger.info(f"Enviando notificação push para tipo: {notification_type}, entidade: {entity}, ação: {action}")

        if notification_type == 'promessa':
            if action in ['criada', 'editada', 'reativada', 'desativada', 'cumprida']:
                titulo = f"Promessa {action.capitalize()}!"
                corpo = f"{entity.usuario.nome_usuario} teve uma promessa {action}."
                destinatarios_ids = set()
                # Adicionar usuários da squad
                if entity.usuario.id_squad:
                    destinatarios_ids.update(cls._obter_destinatarios_squad(entity.usuario.id_squad))
                # Adicionar seguidores (a implementar se necessário e modelo de seguidor existir)
                destinatarios_ids.update(cls._obter_seguidores_usuario(entity.usuario.id_usuario))
                destinatarios_ids.discard(entity.usuario.id_usuario) # Remover o próprio usuário que fez a ação
                cls._enviar_notificacao_para_usuarios(titulo, corpo, list(destinatarios_ids))

        elif notification_type == 'squad':
            if action == 'usuario_adicionado':
                titulo = "Novo membro na Squad!"
                corpo = f"{entity.nome_usuario} chegou devendo..."
                destinatarios_ids = cls._obter_destinatarios_squad(entity.id_squad)
                destinatarios_ids.discard(entity.id_usuario) # Remover o próprio usuário que foi adicionado
                cls._enviar_notificacao_para_usuarios(titulo, corpo, list(destinatarios_ids))

        elif notification_type == 'transacao_pontos':
            if action == 'criada' or action == 'transferencia':
                titulo = "Nova Transação de Pontos"
                corpo = f"Uma nova transação de pontos foi criada/transferida para o usuário '{entity.usuario.nome_usuario}'."
                destinatarios_ids = cls._obter_destinatarios_squad(entity.usuario.id_squad)
                destinatarios_ids.update(cls._obter_seguidores_usuario(entity.usuario.id_usuario))
                destinatarios_ids.discard(entity.usuario.id_usuario) # Remover o próprio usuário que fez a ação
                cls._enviar_notificacao_para_usuarios(titulo, corpo, list(destinatarios_ids))

        elif notification_type == 'regra':
            if action == 'nova_versao_ativada':
                titulo = "Nova Versão de Regra Ativada"
                corpo = "Uma nova versão da regra de pontos foi ativada. Verifique as mudanças."
                destinatarios_ids = cls._obter_destinatarios_todos() # Notificar todos os usuários
                cls._enviar_notificacao_para_usuarios(titulo, corpo, list(destinatarios_ids))
        else:
            logger.warning(f"Tipo de notificação desconhecido: {notification_type}")


    @classmethod
    def _obter_destinatarios_squad(cls, id_squad) -> List[int]:
        """Obtém a lista de IDs dos usuários destinatários de uma squad"""
        with get_scoped_session() as session:
            return [
                id for (id,) in
                session.query(Usuario.id_usuario).filter_by(
                    id_squad=id_squad,
                    is_ativo=True
                ).all()
            ]

    @classmethod
    def _obter_destinatarios_todos(cls) -> List[int]:
        """Obtém a lista de IDs de todos os usuários ativos"""
        with get_scoped_session() as session:
            return [
                id for (id,) in
                session.query(Usuario.id_usuario).filter_by(is_ativo=True).all()
            ]

    @classmethod
    def _obter_seguidores_usuario(cls, id_usuario) -> List[int]:
        """Obtém a lista de IDs dos usuários seguidores de um usuário."""
        # Implemente a lógica para obter seguidores aqui
        # Este é um exemplo, você precisará adaptar para o seu modelo de dados
        with get_scoped_session() as session:
            usuario = session.query(Usuario).get(id_usuario)
            if not usuario:
                return []
            # Assumindo que existe um relacionamento 'seguidores' no modelo Usuario
            seguidores_ids = [seguidor.id_usuario for seguidor in usuario.seguidores] # Adapte conforme seu modelo
            return seguidores_ids


    @classmethod
    def _enviar_notificacao_para_usuarios(cls, titulo, corpo, destinatarios_ids: List[int], entity=None):
        """Cria e envia notificação para uma lista de usuários"""
        if not destinatarios_ids:
            logger.info("Sem destinatários para enviar notificação push.")
            return

        logger.info(f"Criando notificação push '{titulo}' para {len(destinatarios_ids)} usuários.")
        
        id_squad_destino = None
        if entity and hasattr(entity, 'usuario') and entity.usuario and entity.usuario.id_squad:
            id_squad_destino = entity.usuario.id_squad

        publico_alvo_value = PublicoAlvo.SQUAD.value if id_squad_destino else PublicoAlvo.TODOS.value # Define publico_alvo dinamicamente
        notificacao = NotificationService.criar_notificacao(
            titulo=titulo,
            corpo=corpo,
            publico_alvo=publico_alvo_value,
            id_usuario_criador=1, #TODO: Ajustar usuario criador system?
            id_squad_destino=id_squad_destino
        )
        for id_usuario in destinatarios_ids:
             NotificationService.enviar_notificacao(notificacao.id_notificacao)

    @classmethod
    def notificar_nova_promessa(cls, promessa):
        """Envia notificação push para nova promessa."""
        cls.send_push_notification('promessa', promessa, 'criada')

    @classmethod
    def notificar_promessa_alterada(cls, promessa, action):
        """Envia notificação push para promessa alterada (editada, desativada, reativada, cumprida)."""
        cls.send_push_notification('promessa', promessa, action)

    @classmethod
    def notificar_usuario_adicionado_squad(cls, usuario):
        """Envia notificação push para usuário adicionado a squad."""
        cls.send_push_notification('squad', usuario, 'usuario_adicionado')

    @classmethod
    def notificar_nova_transacao_pontos(cls, transacao_pontos):
        """Envia notificação push para nova transação de pontos."""
        cls.send_push_notification('transacao_pontos', transacao_pontos, 'criada')

    @classmethod
    def notificar_transferencia_pontos(cls, transacao_pontos):
        """Envia notificação push para transferência de pontos."""
        cls.send_push_notification('transacao_pontos', transacao_pontos, 'transferencia')

    @classmethod
    def notificar_nova_versao_regra(cls):
        """Envia notificação push para nova versão de regra ativada."""
        cls.send_push_notification('regra', None, 'nova_versao_ativada')
