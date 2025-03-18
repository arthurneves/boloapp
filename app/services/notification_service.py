from app import db
from app.models.notification import Notification, NotificacaoEnviada, StatusEnvio, PublicoAlvo
from app.models.usuario import Usuario
from app.models.squad import Squad
from app.models.promessa import Promessa, StatusPromessa
from app.models.transacao_pontos import TransacaoPontos
from app.models.transferencia_bolos import TransferenciaBolos
from app.models.regra import Regra
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
import json
import logging
from pywebpush import webpush, WebPushException
from app.models.push_subscription import PushSubscription
import os

logger = logging.getLogger(__name__)

def _load_vapid_keys():
    """Carrega e valida as chaves VAPID"""
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    import base64

    private_key_b64 = os.getenv('VAPID_PRIVATE_KEY')
    public_key_b64 = os.getenv('VAPID_PUBLIC_KEY')
    claim_email = os.getenv('VAPID_CLAIM_EMAIL', 'admin@example.com')

    if not private_key_b64 or not public_key_b64:
        logger.error("Chaves VAPID não encontradas! Execute python config/generate_keys.py")
        raise ValueError("Chaves VAPID não configuradas")

    try:
        # Processar chave privada
        private_key = private_key_b64.strip()
        private_key = private_key.replace('-----BEGIN PRIVATE KEY-----', '')
        private_key = private_key.replace('-----END PRIVATE KEY-----', '')
        private_key = private_key.replace('\n', '')
        private_key = private_key.strip()
        
        # Processar chave pública
        public_key = public_key_b64.strip()
        if public_key.startswith('-----BEGIN PUBLIC KEY-----'):
            public_key = public_key.replace('-----BEGIN PUBLIC KEY-----', '')
            public_key = public_key.replace('-----END PUBLIC KEY-----', '')
            public_key = public_key.replace('\n', '')
            public_key = public_key.strip()
        
        # Log do processamento
        logger.info("Chaves VAPID processadas com sucesso")
        logger.debug(f"Private key length: {len(private_key)}")
        logger.debug(f"Public key length: {len(public_key)}")
        
        # Garantir que ambas as chaves são válidas base64url
        private_key = private_key.replace('+', '-').replace('/', '_')
        public_key = public_key.replace('+', '-').replace('/', '_')
        
        return {
            'private_key': private_key,
            'public_key': public_key,
            'claims': {"sub": f"mailto:{claim_email}"}
        }
    except Exception as e:
        logger.error(f"Erro ao processar chaves VAPID: {str(e)}")
        raise ValueError(f"Erro ao processar chaves VAPID: {str(e)}")

# Carregar configurações VAPID
try:
    VAPID_KEYS = _load_vapid_keys()
except Exception as e:
    logger.error(f"Erro ao carregar chaves VAPID: {str(e)}")
    VAPID_KEYS = None

# Expor a chave pública VAPID para uso no frontend
@property
def vapid_public_key():
    if VAPID_KEYS:
        return VAPID_KEYS['public_key']
    return None

class NotificationService:
    @classmethod
    def get_vapid_public_key(cls):
        """Retorna a chave pública VAPID para uso no frontend"""
        if VAPID_KEYS:
            return VAPID_KEYS['public_key']
        return None
    @staticmethod
    def criar_notificacao(titulo, corpo, publico_alvo, id_usuario_criador, 
                         id_usuario_destino=None, id_squad_destino=None, 
                         agendamento=None, is_ativo=True):
        """
        Cria uma nova notificação no sistema
        """
        try:
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
            
            db.session.add(notificacao)
            db.session.commit()
            
            # Se não houver agendamento, enviar imediatamente
            if not agendamento and is_ativo:
                NotificationService.enviar_notificacao(notificacao.id_notificacao)
            
            return notificacao
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar notificação: {str(e)}")
            raise
    
    @staticmethod
    def atualizar_notificacao(id_notificacao, titulo=None, corpo=None, publico_alvo=None,
                             id_usuario_destino=None, id_squad_destino=None, 
                             agendamento=None, is_ativo=None):
        """
        Atualiza uma notificação existente
        """
        try:
            notificacao = Notification.query.get(id_notificacao)
            
            if not notificacao:
                raise ValueError(f"Notificação com ID {id_notificacao} não encontrada")
            
            # Só permite atualizar notificações pendentes
            if notificacao.status_envio != StatusEnvio.PENDENTE.value:
                raise ValueError("Não é possível atualizar uma notificação que já foi enviada")
            
            if titulo is not None:
                notificacao.titulo_notificacao = titulo
            
            if corpo is not None:
                notificacao.corpo_notificacao = corpo
            
            if publico_alvo is not None:
                notificacao.publico_alvo = publico_alvo
                
                # Resetar os campos de destino se o público-alvo mudar
                if publico_alvo != PublicoAlvo.USUARIO_ESPECIFICO.value:
                    notificacao.id_usuario_destino = None
                
                if publico_alvo != PublicoAlvo.SQUAD.value:
                    notificacao.id_squad_destino = None
            
            if id_usuario_destino is not None and notificacao.publico_alvo == PublicoAlvo.USUARIO_ESPECIFICO.value:
                notificacao.id_usuario_destino = id_usuario_destino
            
            if id_squad_destino is not None and notificacao.publico_alvo == PublicoAlvo.SQUAD.value:
                notificacao.id_squad_destino = id_squad_destino
            
            if agendamento is not None:
                notificacao.agendamento = agendamento
            
            if is_ativo is not None:
                notificacao.is_ativo = is_ativo
            
            db.session.commit()
            
            # Se a notificação foi ativada e não tem agendamento, enviar imediatamente
            if is_ativo and notificacao.is_ativo and not notificacao.agendamento:
                NotificationService.enviar_notificacao(notificacao.id_notificacao)
            
            return notificacao
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar notificação: {str(e)}")
            raise
    
    @staticmethod
    def enviar_notificacao(id_notificacao):
        """
        Envia uma notificação para os destinatários
        """
        try:
            notificacao = Notification.query.get(id_notificacao)
            
            if not notificacao:
                raise ValueError(f"Notificação com ID {id_notificacao} não encontrada")
            
            if not notificacao.is_ativo:
                logger.info(f"Notificação {id_notificacao} está inativa, não será enviada")
                return False
            
            # Verificar se a notificação já foi enviada
            if notificacao.status_envio == StatusEnvio.ENVIADO.value:
                logger.info(f"Notificação {id_notificacao} já foi enviada anteriormente")
                return True
            
            # Verificar se é uma notificação agendada e ainda não chegou o momento
            if notificacao.agendamento and notificacao.agendamento > datetime.now():
                logger.info(f"Notificação {id_notificacao} está agendada para {notificacao.agendamento}, não será enviada agora")
                return False
            
            # Obter os destinatários com base no público-alvo
            destinatarios = NotificationService._obter_destinatarios(notificacao)
            
            # Filtrar destinatários que já receberam 3 notificações hoje
            destinatarios_filtrados = []
            for usuario in destinatarios:
                if NotificacaoEnviada.get_notificacoes_enviadas_hoje(usuario.id_usuario) < 300: #TODO:  Voltar para 3
                    destinatarios_filtrados.append(usuario)
            
            # Enviar a notificação para cada destinatário
            for usuario in destinatarios_filtrados:
                try:
                    # Registrar o envio
                    notificacao_enviada = NotificacaoEnviada(
                        id_notificacao=notificacao.id_notificacao,
                        id_usuario=usuario.id_usuario
                    )
                    db.session.add(notificacao_enviada)
                    
                    # Preparar dados da notificação
                    notification_data = {
                        "title": notificacao.titulo_notificacao,
                        "body": notificacao.corpo_notificacao,
                        "url": f"/notificacoes/{notificacao.id_notificacao}/detalhes"
                    }
                    
                    # Buscar todas as subscrições ativas do usuário
                    subscriptions = PushSubscription.query.filter_by(
                        id_usuario=usuario.id_usuario,
                        is_ativo=True
                    ).all()
                    
                    for subscription in subscriptions:
                        try:
                            if not VAPID_KEYS:
                                raise ValueError("Chaves VAPID não configuradas corretamente")
                                
                            webpush(
                                subscription_info=subscription.to_web_push_data(),
                                data=json.dumps(notification_data),
                                vapid_private_key=VAPID_KEYS['private_key'],
                                vapid_claims=VAPID_KEYS['claims']
                            )
                            logger.info(f"Notificação {id_notificacao} enviada com sucesso para o dispositivo {subscription.id} do usuário {usuario.id_usuario}")
                        except WebPushException as e:
                            logger.error(f"Erro ao enviar notificação push: {str(e)}")
                            if e.response and e.response.status_code == 410:
                                # Subscription expirada
                                subscription.is_ativo = False
                                db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar notificação {id_notificacao} para o usuário {usuario.id_usuario}: {str(e)}")
            
            # Atualizar o status da notificação
            notificacao.status_envio = StatusEnvio.ENVIADO.value
            notificacao.data_envio = datetime.now()
            
            db.session.commit()
            return True
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao enviar notificação: {str(e)}")
            
            # Marcar a notificação como falha
            try:
                notificacao = Notification.query.get(id_notificacao)
                if notificacao:
                    notificacao.status_envio = StatusEnvio.FALHA.value
                    db.session.commit()
            except:
                db.session.rollback()
            
            raise
    
    @staticmethod
    def _obter_destinatarios(notificacao):
        """
        Obtém a lista de usuários destinatários com base no público-alvo da notificação
        """
        if notificacao.publico_alvo == PublicoAlvo.TODOS.value:
            return Usuario.query.filter_by(is_ativo=True).all()
        
        elif notificacao.publico_alvo == PublicoAlvo.USUARIO_ESPECIFICO.value:
            if not notificacao.id_usuario_destino:
                return []
            
            usuario = Usuario.query.get(notificacao.id_usuario_destino)
            return [usuario] if usuario and usuario.is_ativo else []
        
        elif notificacao.publico_alvo == PublicoAlvo.SQUAD.value:
            if not notificacao.id_squad_destino:
                return []
            
            return Usuario.query.filter_by(
                id_squad=notificacao.id_squad_destino,
                is_ativo=True
            ).all()
        
        return []
    
    @staticmethod
    def processar_notificacoes_agendadas():
        """
        Processa todas as notificações agendadas que estão prontas para envio
        """
        try:
            # Buscar notificações agendadas que estão ativas, pendentes e com agendamento no passado
            notificacoes = Notification.query.filter(
                Notification.is_ativo == True,
                Notification.status_envio == StatusEnvio.PENDENTE.value,
                Notification.agendamento <= datetime.now()
            ).all()
            
            for notificacao in notificacoes:
                try:
                    NotificationService.enviar_notificacao(notificacao.id_notificacao)
                except Exception as e:
                    logger.error(f"Erro ao processar notificação agendada {notificacao.id_notificacao}: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao processar notificações agendadas: {str(e)}")
            return False
    
    # Métodos para notificações automáticas
    
    @staticmethod
    def notificar_nova_promessa(promessa):
        """
        Notifica usuários sobre uma nova promessa criada
        """
        try:
            # Obter o usuário da promessa
            usuario = Usuario.query.get(promessa.id_usuario)
            if not usuario or not usuario.is_ativo:
                return False
            
            # Obter usuários da mesma squad
            usuarios_squad = []
            if usuario.id_squad:
                usuarios_squad = Usuario.query.filter(
                    Usuario.id_squad == usuario.id_squad,
                    Usuario.id_usuario != usuario.id_usuario,
                    Usuario.is_ativo == True
                ).all()
            
            # Obter seguidores do usuário
            seguidores = usuario.seguidores.filter(Usuario.is_ativo == True).all()
            
            # Combinar e remover duplicatas
            destinatarios = list(set(usuarios_squad + seguidores))
            
            # Criar a notificação
            titulo = "Nova promessa criada"
            corpo = f"{usuario.nome_usuario} criou uma nova promessa: {promessa.titulo_promessa}"
            
            # Criar notificação para cada destinatário
            for destinatario in destinatarios:
                # Verificar limite diário
                if NotificacaoEnviada.get_notificacoes_enviadas_hoje(destinatario.id_usuario) < 300:
                    NotificationService.criar_notificacao(
                        titulo=titulo,
                        corpo=corpo,
                        publico_alvo=PublicoAlvo.USUARIO_ESPECIFICO.value,
                        id_usuario_criador=1,  # ID do sistema
                        id_usuario_destino=destinatario.id_usuario
                    )
            
            return True
        except Exception as e:
            logger.error(f"Erro ao notificar nova promessa: {str(e)}")
            return False
    
    @staticmethod
    def notificar_promessa_alterada(promessa, tipo_alteracao):
        """
        Notifica usuários sobre alterações em uma promessa
        """
        try:
            # Obter o usuário da promessa
            usuario = Usuario.query.get(promessa.id_usuario)
            if not usuario or not usuario.is_ativo:
                return False
            
            # Obter usuários da mesma squad
            usuarios_squad = []
            if usuario.id_squad:
                usuarios_squad = Usuario.query.filter(
                    Usuario.id_squad == usuario.id_squad,
                    Usuario.id_usuario != usuario.id_usuario,
                    Usuario.is_ativo == True
                ).all()
            
            # Obter seguidores do usuário
            seguidores = usuario.seguidores.filter(Usuario.is_ativo == True).all()
            
            # Combinar e remover duplicatas
            destinatarios = list(set(usuarios_squad + seguidores))
            
            # Definir título e corpo com base no tipo de alteração
            if tipo_alteracao == 'editada':
                titulo = "Promessa atualizada"
                corpo = f"{usuario.nome_usuario} atualizou a promessa: {promessa.titulo_promessa}"
            elif tipo_alteracao == 'desativada':
                titulo = "Promessa desativada"
                corpo = f"{usuario.nome_usuario} desativou a promessa: {promessa.titulo_promessa}"
            elif tipo_alteracao == 'reativada':
                titulo = "Promessa reativada"
                corpo = f"{usuario.nome_usuario} reativou a promessa: {promessa.titulo_promessa}"
            elif tipo_alteracao == 'cumprida':
                titulo = "Promessa cumprida"
                corpo = f"{usuario.nome_usuario} cumpriu a promessa: {promessa.titulo_promessa}"
            else:
                return False
            
            # Criar notificação para cada destinatário
            for destinatario in destinatarios:
                # Verificar limite diário
                if NotificacaoEnviada.get_notificacoes_enviadas_hoje(destinatario.id_usuario) < 3:
                    NotificationService.criar_notificacao(
                        titulo=titulo,
                        corpo=corpo,
                        publico_alvo=PublicoAlvo.USUARIO_ESPECIFICO.value,
                        id_usuario_criador=1,  # ID do sistema
                        id_usuario_destino=destinatario.id_usuario
                    )
            
            return True
        except Exception as e:
            logger.error(f"Erro ao notificar alteração de promessa: {str(e)}")
            return False
    
    @staticmethod
    def notificar_usuario_adicionado_squad(usuario_id, squad_id):
        """
        Notifica usuários quando um novo membro é adicionado ao squad
        """
        try:
            # Obter o usuário adicionado
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not usuario.is_ativo:
                return False
            
            # Obter o squad
            squad = Squad.query.get(squad_id)
            if not squad or not squad.is_ativo:
                return False
            
            # Obter outros usuários do squad
            usuarios_squad = Usuario.query.filter(
                Usuario.id_squad == squad_id,
                Usuario.id_usuario != usuario_id,
                Usuario.is_ativo == True
            ).all()
            
            # Criar a notificação
            titulo = "Novo membro no squad"
            corpo = f"{usuario.nome_usuario} foi adicionado ao squad {squad.titulo_squad}"
            
            # Criar notificação para cada membro do squad
            for destinatario in usuarios_squad:
                # Verificar limite diário
                if NotificacaoEnviada.get_notificacoes_enviadas_hoje(destinatario.id_usuario) < 3:
                    NotificationService.criar_notificacao(
                        titulo=titulo,
                        corpo=corpo,
                        publico_alvo=PublicoAlvo.USUARIO_ESPECIFICO.value,
                        id_usuario_criador=1,  # ID do sistema
                        id_usuario_destino=destinatario.id_usuario
                    )
            
            return True
        except Exception as e:
            logger.error(f"Erro ao notificar adição de usuário ao squad: {str(e)}")
            return False
    
    @staticmethod
    def notificar_nova_transacao(transacao):
        """
        Notifica usuários sobre uma nova transação de pontos
        """
        try:
            # Obter o usuário da transação
            usuario = Usuario.query.get(transacao.id_usuario)
            if not usuario or not usuario.is_ativo:
                return False
            
            # Obter usuários da mesma squad
            usuarios_squad = []
            if usuario.id_squad:
                usuarios_squad = Usuario.query.filter(
                    Usuario.id_squad == usuario.id_squad,
                    Usuario.id_usuario != usuario.id_usuario,
                    Usuario.is_ativo == True
                ).all()
            
            # Criar a notificação
            titulo = "Nova transação de pontos"
            corpo = f"{usuario.nome_usuario} recebeu {transacao.pontos_transacao} pontos: {transacao.descricao_transacao}"
            
            # Criar notificação para cada membro do squad
            for destinatario in usuarios_squad:
                # Verificar limite diário
                if NotificacaoEnviada.get_notificacoes_enviadas_hoje(destinatario.id_usuario) < 3:
                    NotificationService.criar_notificacao(
                        titulo=titulo,
                        corpo=corpo,
                        publico_alvo=PublicoAlvo.USUARIO_ESPECIFICO.value,
                        id_usuario_criador=1,  # ID do sistema
                        id_usuario_destino=destinatario.id_usuario
                    )
            
            return True
        except Exception as e:
            logger.error(f"Erro ao notificar nova transação: {str(e)}")
            return False
    
    @staticmethod
    def notificar_transferencia_pontos(transferencia):
        """
        Notifica usuários sobre uma transferência de pontos
        """
        try:
            # Obter os usuários envolvidos
            usuario_origem = Usuario.query.get(transferencia.usuario_origem_id)
            usuario_destino = Usuario.query.get(transferencia.usuario_destino_id)
            
            if not usuario_origem or not usuario_destino:
                return False
            
            # Obter usuários da mesma squad do usuário de origem
            usuarios_squad_origem = []
            if usuario_origem.id_squad:
                usuarios_squad_origem = Usuario.query.filter(
                    Usuario.id_squad == usuario_origem.id_squad,
                    Usuario.id_usuario != usuario_origem.id_usuario,
                    Usuario.id_usuario != usuario_destino.id_usuario,
                    Usuario.is_ativo == True
                ).all()
            
            # Obter usuários da mesma squad do usuário de destino
            usuarios_squad_destino = []
            if usuario_destino.id_squad and usuario_destino.id_squad != usuario_origem.id_squad:
                usuarios_squad_destino = Usuario.query.filter(
                    Usuario.id_squad == usuario_destino.id_squad,
                    Usuario.id_usuario != usuario_destino.id_usuario,
                    Usuario.id_usuario != usuario_origem.id_usuario,
                    Usuario.is_ativo == True
                ).all()
            
            # Combinar e remover duplicatas
            destinatarios = list(set(usuarios_squad_origem + usuarios_squad_destino))
            
            # Criar a notificação
            titulo = "Transferência de pontos"
            corpo = f"{usuario_origem.nome_usuario} transferiu {transferencia.valor} pontos para {usuario_destino.nome_usuario}"
            
            # Criar notificação para cada destinatário
            for destinatario in destinatarios:
                # Verificar limite diário
                if NotificacaoEnviada.get_notificacoes_enviadas_hoje(destinatario.id_usuario) < 3:
                    NotificationService.criar_notificacao(
                        titulo=titulo,
                        corpo=corpo,
                        publico_alvo=PublicoAlvo.USUARIO_ESPECIFICO.value,
                        id_usuario_criador=1,  # ID do sistema
                        id_usuario_destino=destinatario.id_usuario
                    )
            
            return True
        except Exception as e:
            logger.error(f"Erro ao notificar transferência de pontos: {str(e)}")
            return False
    
    @staticmethod
    def notificar_nova_regra(regra):
        """
        Notifica todos os usuários sobre uma nova versão de regra ativada
        """
        try:
            # Criar a notificação
            titulo = "Nova versão de regras"
            corpo = "Uma nova versão das regras de pontos foi ativada. Confira as atualizações!"
            
            # Notificar todos os usuários ativos
            NotificationService.criar_notificacao(
                titulo=titulo,
                corpo=corpo,
                publico_alvo=PublicoAlvo.TODOS.value,
                id_usuario_criador=1  # ID do sistema
            )
            
            return True
        except Exception as e:
            logger.error(f"Erro ao notificar nova regra: {str(e)}")
            return False
