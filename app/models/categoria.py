from app import db
from datetime import datetime

class Categoria(db.Model):
    __tablename__ = 'categoria'
    
    id_categoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo_categoria = db.Column(db.String(100), nullable=False)
    descricao_categoria = db.Column(db.Text, nullable=True)
    is_ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_edicao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id_categoria': self.id_categoria,
            'titulo_categoria': self.titulo_categoria,
            'descricao_categoria': self.descricao_categoria,
            'is_ativo': self.is_ativo,
            'data_criacao': self.data_criacao.isoformat(),
            'data_edicao': self.data_edicao.isoformat()
        }
