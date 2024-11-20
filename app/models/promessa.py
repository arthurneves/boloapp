from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class Promessa(db.Model):
    __tablename__ = 'promessa'
    
    id_promessa = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    titulo_promessa = db.Column(db.String(255), nullable=False)
    descricao_promessa = db.Column(db.Text, nullable=True)
    is_ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_edicao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com Usuário
    usuario = db.relationship('Usuario')

    @validates('titulo_promessa')
    def validate_titulo_promessa(self, key, titulo):
        # Validações mais robustas para o título
        if not titulo:
            raise ValueError("Título da promessa é obrigatório")
        
        # Remove espaços extras
        titulo = titulo.strip()
        
        # Verifica comprimento
        if len(titulo) < 3:
            raise ValueError("Título da promessa deve ter pelo menos 3 caracteres")
        
        return titulo

    @validates('descricao_promessa')
    def validate_descricao_promessa(self, key, descricao):
        # Validação opcional para descrição
        if descricao:
            descricao = descricao.strip()
            if len(descricao) > 1000:
                raise ValueError("Descrição não pode exceder 1000 caracteres")
        
        return descricao

    def __repr__(self):
        return f'<Promessa {self.titulo_promessa} (ID: {self.id_promessa})>'

    def to_dict(self):
        return {
            'id_promessa': self.id_promessa,
            'id_usuario': self.id_usuario,
            'titulo_promessa': self.titulo_promessa,
            'descricao_promessa': self.descricao_promessa,
            'is_ativo': self.is_ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_edicao': self.data_edicao.isoformat() if self.data_edicao else None,
            'usuario': self.usuario.nome_usuario if self.usuario else None
        }

    def desativar(self):
        """
        Método para desativar a promessa
        """
        self.is_ativo = False
