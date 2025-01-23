from app import db
from datetime import datetime

class Regra(db.Model):
    id_regra = db.Column(db.Integer, primary_key=True)
    conteudo_regras = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_edicao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_ativo = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Regra {self.id_regra}>'
