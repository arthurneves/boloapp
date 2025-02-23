from app import db
from sqlalchemy import event, func

class TransferenciaBolos(db.Model):
    __tablename__ = 'transferencia_bolos'
    
    id_transferencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_origem_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    usuario_destino_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    valor = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    data_transferencia = db.Column(db.DateTime, server_default=func.now())

    # Relacionamentos
    usuario_origem = db.relationship('Usuario', foreign_keys=[usuario_origem_id])
    usuario_destino = db.relationship('Usuario', foreign_keys=[usuario_destino_id])

    def to_dict(self):
        return {
            'id_transferencia': self.id_transferencia,
            'usuario_origem_id': self.usuario_origem_id,
            'usuario_destino_id': self.usuario_destino_id,
            'valor': self.valor,
            'descricao': self.descricao,
            'data_transferencia': self.data_transferencia.isoformat(),
            'usuario_origem': self.usuario_origem.nome_usuario,
            'usuario_destino': self.usuario_destino.nome_usuario
        }

    @staticmethod
    def registrar_transferencia(usuario_origem_id, usuario_destino_id, valor, descricao=None):
        """
        Método estático para registrar uma nova transferência e criar os registros 
        correspondentes na tabela transacao_pontos
        """
        from app.models.transacao_pontos import TransacaoPontos
        from app.models.log import Log
        
        # Criar registro da transferência
        transferencia = TransferenciaBolos(
            usuario_origem_id=usuario_origem_id,
            usuario_destino_id=usuario_destino_id,
            valor=valor,
            descricao=descricao
        )
        
        # Preparar descrições para as transações
        descricao_base = f"{descricao + ' - ' if descricao else ''}"
        
        # Criar registros de transação de pontos
        debito = TransacaoPontos(
            id_usuario=usuario_origem_id,
            id_categoria=1,  # TODO: Definir categoria padrão para transferências
            pontos_transacao=-valor,  # Valor negativo para débito
            descricao_transacao=f"{descricao_base}Transferência de {valor} bolos para usuário ID {usuario_destino_id}"
        )
        
        credito = TransacaoPontos(
            id_usuario=usuario_destino_id,
            id_categoria=1,  # TODO: Definir categoria padrão para transferências
            pontos_transacao=valor,  # Valor positivo para crédito
            descricao_transacao=f"{descricao_base}Recebimento de {valor} bolos do usuário ID {usuario_origem_id}"
        )
        
        db.session.add(transferencia)
        db.session.add(debito)
        db.session.add(credito)
        db.session.commit()
        
        # Registrar log da transferência
        Log.criar_log(transferencia.id_transferencia, 'transferencia_bolos', 'transferir', usuario_origem_id)
        
        return transferencia, debito, credito
