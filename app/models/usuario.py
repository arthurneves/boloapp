from app import db
from datetime import datetime

class Usuario(db.Model):
    __tablename__ = 'usuario'
    
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_usuario = db.Column(db.String(100), nullable=False)
    email_usuario = db.Column(db.String(100), unique=True, nullable=False)
    is_ativo = db.Column(db.Boolean, default=True)
    is_administrador = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_edicao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'nome_usuario': self.nome_usuario,
            'email_usuario': self.email_usuario,
            'is_ativo': self.is_ativo,
            'is_administrador': self.is_administrador,
            'data_criacao': self.data_criacao.isoformat(),
            'data_edicao': self.data_edicao.isoformat()
        }
