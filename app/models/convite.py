from app import db
from datetime import datetime

class Convite(db.Model):
    id_convite = db.Column(db.Integer, primary_key=True)
    hash_convite = db.Column(db.String(10), unique=True, nullable=False)
    id_usuario_responsavel = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_usuario_cadastrado = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_usuario_cadastrado = db.Column(db.DateTime)
    is_ativo = db.Column(db.Boolean, default=True)

    usuario_responsavel = db.relationship('Usuario', foreign_keys=[id_usuario_responsavel])
    usuario_cadastrado = db.relationship('Usuario', foreign_keys=[id_usuario_cadastrado])

    def __repr__(self):
        return f'<Convite {self.hash_convite}>'
