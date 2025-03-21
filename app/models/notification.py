from app import db
from sqlalchemy import func, Enum as SQLEnum
from sqlalchemy.orm import validates
import enum

class PublicoAlvo(enum.Enum):
    TODOS = "todos"
    USUARIO_ESPECIFICO = "usuario_especifico"
    SQUAD = "squad"

class StatusEnvio(enum.Enum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    ENVIADO = "enviado"
    ENVIADO_PARCIAL = "enviado_parcial"
    FALHA = "falha"

class Notification(db.Model):
    __tablename__ = 'notificacao'
    
    id_notificacao = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo_notificacao = db.Column(db.String(100), nullable=False)
    corpo_notificacao = db.Column(db.Text, nullable=False)
    publico_alvo = db.Column(db.String(50), nullable=False)
    agendamento = db.Column(db.DateTime, nullable=True)
    id_usuario_criador = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    data_envio = db.Column(db.DateTime, nullable=True)
    status_envio = db.Column(db.String(20), default=StatusEnvio.PENDENTE.value)
    is_ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=func.now())
    data_edicao = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    total_enviados = db.Column(db.Integer, default=0)
    total_falhas = db.Column(db.Integer, default=0)
    
    # Campos adicionais para público-alvo específico
    id_usuario_destino = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=True)
    id_squad_destino = db.Column(db.Integer, db.ForeignKey('squad.id_squad'), nullable=True)
    
    # Relacionamentos
    usuario_criador = db.relationship('Usuario', foreign_keys=[id_usuario_criador])
    usuario_destino = db.relationship('Usuario', foreign_keys=[id_usuario_destino])
    squad_destino = db.relationship('Squad', foreign_keys=[id_squad_destino])
    
    # Tabela de associação para rastrear notificações enviadas por usuário
    notificacoes_enviadas = db.relationship(
        'NotificacaoEnviada',
        back_populates='notificacao',
        cascade='all, delete-orphan'
    )
    
    @validates('titulo_notificacao')
    def validate_titulo_notificacao(self, key, titulo):
        if not titulo:
            raise ValueError("Título da notificação é obrigatório")
        
        titulo = titulo.strip()
        
        if len(titulo) < 3:
            raise ValueError("Título da notificação deve ter pelo menos 3 caracteres")
        
        return titulo
    
    @validates('corpo_notificacao')
    def validate_corpo_notificacao(self, key, corpo):
        if not corpo:
            raise ValueError("Corpo da notificação é obrigatório")
        
        corpo = corpo.strip()
        
        if len(corpo) < 5:
            raise ValueError("Corpo da notificação deve ter pelo menos 5 caracteres")
        
        return corpo
    
    @validates('publico_alvo')
    def validate_publico_alvo(self, key, publico):
        if publico not in [e.value for e in PublicoAlvo]:
            raise ValueError(f"Público alvo deve ser um dos seguintes: {', '.join([e.value for e in PublicoAlvo])}")
        
        return publico
    
    def to_dict(self):
        return {
            'id_notificacao': self.id_notificacao,
            'titulo_notificacao': self.titulo_notificacao,
            'corpo_notificacao': self.corpo_notificacao,
            'publico_alvo': self.publico_alvo,
            'agendamento': self.agendamento.isoformat() if self.agendamento else None,
            'id_usuario_criador': self.id_usuario_criador,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None,
            'status_envio': self.status_envio,
            'is_ativo': self.is_ativo,
            'data_criacao': self.data_criacao.isoformat(),
            'data_edicao': self.data_edicao.isoformat(),
            'id_usuario_destino': self.id_usuario_destino,
            'id_squad_destino': self.id_squad_destino,
            'usuario_criador': self.usuario_criador.nome_usuario if self.usuario_criador else None,
            'usuario_destino': self.usuario_destino.nome_usuario if self.usuario_destino else None,
            'squad_destino': self.squad_destino.titulo_squad if self.squad_destino else None,
            'total_enviados': self.total_enviados,
            'total_falhas': self.total_falhas
        }

class NotificacaoEnviada(db.Model):
    __tablename__ = 'notificacao_enviada'
    
    id_notificacao = db.Column(db.Integer, db.ForeignKey('notificacao.id_notificacao'), primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), primary_key=True)
    data_envio = db.Column(db.DateTime, default=func.now())
    
    # Relacionamentos
    notificacao = db.relationship('Notification', back_populates='notificacoes_enviadas')
    usuario = db.relationship('Usuario')
    
    @staticmethod
    def get_notificacoes_enviadas_hoje(id_usuario):
        """
        Retorna o número de notificações enviadas para um usuário hoje
        """
        from datetime import datetime, timedelta
        
        hoje = datetime.now().date()
        amanha = hoje + timedelta(days=1)
        
        return NotificacaoEnviada.query.filter(
            NotificacaoEnviada.id_usuario == id_usuario,
            NotificacaoEnviada.data_envio >= hoje,
            NotificacaoEnviada.data_envio < amanha
        ).count()
