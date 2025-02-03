from app import db
from sqlalchemy import func
from flask_login import current_user

class Log(db.Model):
    __tablename__ = 'log'

    id_log = db.Column(db.Integer, primary_key=True)
    id_usuario_autor = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_usuario_afetado = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=True)
    id_registro_afetado = db.Column(db.Integer, nullable=False)
    tipo_entidade = db.Column(db.String(30), nullable=False)
    acao_log = db.Column(db.String(50), nullable=False)
    data_criacao = db.Column(db.DateTime, default=func.now())

    usuario_autor = db.relationship('Usuario', foreign_keys=[id_usuario_autor], back_populates='logs_criados')
    usuario_afetado = db.relationship('Usuario', foreign_keys=[id_usuario_afetado], back_populates='logs_recebidos')

    def __repr__(self):
        return f'<Log {self.id_log}: {self.acao_log} by {self.id_usuario_autor} on {self.data_criacao}>'

    @classmethod
    def criar_log(cls, id_registro_afetado, tipo_entidade, acao, usuario_afetado=None, id_usuario_autor=None):

        novo_log = cls(
            id_usuario_autor = id_usuario_autor if id_usuario_autor else current_user.id_usuario,
            id_usuario_afetado=usuario_afetado,
            id_registro_afetado = id_registro_afetado,
            tipo_entidade = tipo_entidade,
            acao_log = acao
        )
        db.session.add(novo_log)
        db.session.commit()
        return novo_log
