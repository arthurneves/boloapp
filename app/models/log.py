from app import db
from sqlalchemy import func

class Log(db.Model):
    __tablename__ = 'log'

    id_log = db.Column(db.Integer, primary_key=True)
    id_usuario_autor = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_usuario_afetado = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    acao_log = db.Column(db.String(50), nullable=False)
    data_criacao = db.Column(db.DateTime, default=func.now())

    usuario_autor = db.relationship('Usuario', foreign_keys=[id_usuario_autor], backref='logs_autor')
    usuario_afetado = db.relationship('Usuario', foreign_keys=[id_usuario_afetado], backref='logs_afetado')

    def __repr__(self):
        return f'<Log {self.id_log}: {self.acao_log} by {self.id_usuario_autor} on {self.data_criacao}>'

    @classmethod
    def criar_log(cls, usuario_autor, usuario_afetado, acao):
        """
        Método de classe para criar um novo log
        :param usuario_autor: Usuário que realizou a ação
        :param usuario_afetado: Usuário afetado pela ação
        :param acao: Tipo de ação realizada (Criação, Edição, Desativação)
        :return: Instância do log criado
        """
        novo_log = cls(
            id_usuario_autor=usuario_autor.id_usuario,
            id_usuario_afetado=usuario_afetado.id_usuario,
            acao_log=acao
        )
        db.session.add(novo_log)
        db.session.commit()
        return novo_log
