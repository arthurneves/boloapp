from app import db
from sqlalchemy import func

class Squad(db.Model):
    __tablename__ = 'squad'
    
    id_squad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo_squad = db.Column(db.String(100), nullable=False)
    is_ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=func.now())
    data_edicao = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamento com usuários
    usuarios = db.relationship('Usuario', back_populates='squad', lazy='dynamic')

    def to_dict(self):
        return {
            'id_squad': self.id_squad,
            'titulo_squad': self.titulo_squad,
            'is_ativo': self.is_ativo,
            'data_criacao': self.data_criacao.isoformat(),
            'data_edicao': self.data_edicao.isoformat()
        }
