from app import db
from sqlalchemy import event, func

class TransacaoPontos(db.Model):
    __tablename__ = 'transacao_pontos'
    
    id_transacao = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categoria.id_categoria'), nullable=False)
    pontos_transacao = db.Column(db.Integer, nullable=False)
    descricao_transacao = db.Column(db.Text, nullable=True)
    is_ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, server_default=func.now())
    id_transferencia = db.Column(db.Integer, db.ForeignKey('transferencia_bolos.id_transferencia'), nullable=True)
    aux_saldo = None
    aux_evento = None
    _saldo_ja_atualizado = False
    
    # Relacionamentos
    usuario = db.relationship('Usuario', back_populates='transacoes_pontos')
    categoria = db.relationship('Categoria')
    transferencia = db.relationship('TransferenciaBolos', foreign_keys=[id_transferencia])

    def to_dict(self):
        return {
            'id_transacao': self.id_transacao,
            'id_usuario': self.id_usuario,
            'id_categoria': self.id_categoria,
            'pontos_transacao': self.pontos_transacao,
            'descricao_transacao': self.descricao_transacao,
            'is_ativo': self.is_ativo,
            'data_criacao': self.data_criacao.isoformat(),
            'usuario': self.usuario.nome_usuario,
            'categoria': self.categoria.titulo_categoria
        }

def update_usuario_pontos(mapper, connection, target):
    """
    Atualiza o saldo de pontos do usuário de forma idempotente,
    evitando atualizações duplicadas do saldo
    """
    from app.models.usuario import Usuario

    # Se não estamos em uma operação de edição e já aplicamos o saldo, não faz nada
    if not (target.aux_evento and target.aux_evento == 'edicao') \
       and getattr(target, '_saldo_ja_atualizado', False):
        return

    if target.aux_evento and target.aux_evento == 'edicao':
        pontos = target.aux_saldo
    elif target.is_ativo is False: #desativacao
        pontos = target.pontos_transacao * (-1)
    else:
        pontos = target.pontos_transacao

    # Obtém o usuário usando a connection fornecida
    usuario_table = Usuario.__table__
    stmt = usuario_table.update().\
        where(usuario_table.c.id_usuario == target.id_usuario).\
        values(
            saldo_pontos_usuario=usuario_table.c.saldo_pontos_usuario + pontos
        )
    connection.execute(stmt)

    # Marca o saldo como já atualizado para operações que não sejam de edição
    if not (target.aux_evento and target.aux_evento == 'edicao'):
        target._saldo_ja_atualizado = True

# Registra os eventos
event.listen(TransacaoPontos, 'after_insert', update_usuario_pontos)
event.listen(TransacaoPontos, 'after_update', update_usuario_pontos)
