from app import db
from datetime import datetime
import json

class PushSubscription(db.Model):
    """Model para armazenar inscrições de notificações push dos usuários"""
    __tablename__ = 'push_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    endpoint = db.Column(db.String(500), nullable=False, index=True, unique=True)
    p256dh = db.Column(db.Text, nullable=False)
    auth = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_ativo = db.Column(db.Boolean, nullable=False, default=True)

    # Relacionamento com o usuário
    usuario = db.relationship('Usuario', backref=db.backref('push_subscriptions', lazy=True))

    @staticmethod
    def create_from_subscription(id_usuario, subscription_json):
        """
        Cria ou atualiza uma inscrição push a partir dos dados do navegador
        """
        print("=== Início do processamento de subscription ===")
        
        try:
            # Parse JSON string se necessário
            if isinstance(subscription_json, str):
                data = json.loads(subscription_json)
            else:
                data = subscription_json
            print("Dados de subscription:", json.dumps(data, indent=2))
            
            # Validação básica dos campos obrigatórios
            if not isinstance(data, dict):
                raise ValueError("Dados de subscription devem ser um objeto")
            
            endpoint = data.get('endpoint')
            if not endpoint:
                raise ValueError("Campo 'endpoint' é obrigatório")
            
            # Validar tamanho do endpoint
            if len(endpoint) > 500:
                raise ValueError("URL do endpoint excede o limite de 500 caracteres")
                
            keys = data.get('keys')
            if not isinstance(keys, dict):
                raise ValueError("Campo 'keys' deve ser um objeto")
                
            if not keys.get('p256dh') or not keys.get('auth'):
                raise ValueError("Campos 'p256dh' e 'auth' são obrigatórios em 'keys'")
            
            # Garantir que a sessão está limpa
            db.session.rollback()
            
            try:
                # Buscar subscription existente usando SELECT ... FOR UPDATE para evitar race conditions
                subscription = PushSubscription.query.filter_by(
                    endpoint=data['endpoint']
                ).with_for_update().first()

                if subscription:
                    print(f"Subscription encontrada: {subscription.id}")
                    print(f"Atualizando subscription existente (ID: {subscription.id})")
                    # Se o usuário mudou, atualizar também
                    subscription.id_usuario = id_usuario
                    # Verificar se houve mudança real nos dados
                    if (subscription.p256dh != keys['p256dh'] or 
                        subscription.auth != keys['auth']):
                        subscription.p256dh = keys['p256dh']
                        subscription.auth = keys['auth']
                        subscription.data_atualizacao = datetime.utcnow()
                    subscription.is_ativo = True
                else:
                    print("Criando nova subscription")
                    subscription = PushSubscription(
                        id_usuario=id_usuario,
                        endpoint=data['endpoint'],
                        p256dh=keys['p256dh'],
                        auth=keys['auth']
                    )
                    db.session.add(subscription)

                # Forçar o flush para detectar erros antes do commit
                db.session.flush()
                
                # Se chegou aqui, commit a transação
                db.session.commit()
                print("Subscription salva com sucesso:", {
                    'id': subscription.id,
                    'endpoint': subscription.endpoint[:50] + "...",
                    'p256dh_length': len(subscription.p256dh),
                    'auth_length': len(subscription.auth),
                    'usuario_id': subscription.id_usuario
                })
                return subscription
            
            except Exception as db_error:
                print("Erro ao salvar no banco:", str(db_error))
                db.session.rollback()
                # Re-raise com mensagem mais descritiva
                raise ValueError(f"Falha ao salvar subscription no banco de dados: {str(db_error)}")
                
        except json.JSONDecodeError as e:
            print("Erro ao decodificar JSON:", str(e))
            raise ValueError(f'JSON inválido: {str(e)}')
        except ValueError as e:
            print("Erro de validação:", str(e))
            raise e
        except Exception as e:
            print("Erro não esperado:", str(e))
            raise ValueError(f'Erro ao processar subscription: {str(e)}')
        finally:
            print("=== Fim do processamento de subscription ===")

    def to_web_push_data(self):
        """
        Converte o modelo para o formato necessário para a biblioteca web-push
        """
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh,
                'auth': self.auth
            }
        }
