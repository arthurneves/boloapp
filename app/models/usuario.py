from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_usuario = db.Column(db.String(100), nullable=False)
    email_usuario = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    saldo_pontos_usuario = db.Column(db.Integer, default=0)
    id_squad = db.Column(db.Integer, db.ForeignKey('squad.id_squad'), nullable=True)
    is_ativo = db.Column(db.Boolean, default=True)
    is_administrador = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_edicao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    squad = db.relationship('Squad', back_populates='usuarios')
    transacoes_pontos = db.relationship('TransacaoPontos', back_populates='usuario', lazy='dynamic', cascade='all, delete-orphan')

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def get_id(self):
        return str(self.id_usuario)

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'nome_usuario': self.nome_usuario,
            'email_usuario': self.email_usuario,
            'saldo_pontos_usuario': self.saldo_pontos_usuario,
            'id_squad': self.id_squad,
            'squad': self.squad.titulo_squad if self.squad else None,
            'is_ativo': self.is_ativo,
            'is_administrador': self.is_administrador,
            'data_criacao': self.data_criacao.isoformat(),
            'data_edicao': self.data_edicao.isoformat()
        }
