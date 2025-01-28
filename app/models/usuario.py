from app import db
from sqlalchemy import func, Table
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Tabela de associação para seguidores
seguidores = Table('seguidor',
    db.Model.metadata,
    db.Column('id_seguidor', db.Integer, db.ForeignKey('usuario.id_usuario'), primary_key=True),
    db.Column('id_seguido', db.Integer, db.ForeignKey('usuario.id_usuario'), primary_key=True),
    db.Column('data_criacao', db.DateTime, default=func.now())
)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_usuario = db.Column(db.String(100), nullable=False)
    login_usuario = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    saldo_pontos_usuario = db.Column(db.Integer, default=0)
    id_squad = db.Column(db.Integer, db.ForeignKey('squad.id_squad'), nullable=True)
    is_ativo = db.Column(db.Boolean, default=True)
    is_administrador = db.Column(db.Boolean, default=False)
    foto_perfil = db.Column(db.String(255), nullable=True)
    data_criacao = db.Column(db.DateTime, default=func.now())
    data_edicao = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    squad = db.relationship('Squad', back_populates='usuarios')
    transacoes_pontos = db.relationship('TransacaoPontos', back_populates='usuario', lazy='dynamic', cascade='all, delete-orphan')
    promessas = db.relationship('Promessa', back_populates='usuario')
    logs_criados = db.relationship('Log', foreign_keys='Log.id_usuario_autor', back_populates='usuario_autor')
    logs_recebidos = db.relationship('Log', foreign_keys='Log.id_usuario_afetado', back_populates='usuario_afetado')
    
    # Relacionamentos de seguidores
    seguindo = db.relationship(
        'Usuario',
        secondary=seguidores,
        primaryjoin=(id_usuario == seguidores.c.id_seguidor),
        secondaryjoin=(id_usuario == seguidores.c.id_seguido),
        backref=db.backref('seguidores', lazy='dynamic'),
        lazy='dynamic'
    )



    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def get_id(self):
        return str(self.id_usuario)

    def seguir(self, usuario):
        if not self.esta_seguindo(usuario):
            self.seguindo.append(usuario)
            return True
        return False

    def deixar_seguir(self, usuario):
        if self.esta_seguindo(usuario):
            self.seguindo.remove(usuario)
            return True
        return False

    def esta_seguindo(self, usuario):
        return self.seguindo.filter(seguidores.c.id_seguido == usuario.id_usuario).count() > 0

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'nome_usuario': self.nome_usuario,
            'login_usuario': self.login_usuario,
            'saldo_pontos_usuario': self.saldo_pontos_usuario,
            'id_squad': self.id_squad,
            'squad': self.squad.titulo_squad if self.squad else None,
            'is_ativo': self.is_ativo,
            'is_administrador': self.is_administrador,
            'foto_perfil': self.foto_perfil,
            'data_criacao': self.data_criacao.isoformat(),
            'data_edicao': self.data_edicao.isoformat()
        }
