from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, SubmitField, SelectField, ValidationError
from wtforms.validators import DataRequired, Length, NumberRange
from app.models.usuario import Usuario

class TransferenciaBolosForm(FlaskForm):
    usuario_origem = SelectField('Usuário Origem (Débito)', coerce=int, validators=[
        DataRequired(message='Selecione o usuário de origem')
    ])
    usuario_destino = SelectField('Usuário Destino (Crédito)', coerce=int, validators=[
        DataRequired(message='Selecione o usuário de destino')
    ])
    valor_transferencia = IntegerField('Valor a Transferir', validators=[
        DataRequired(message='Valor é obrigatório'),
        NumberRange(min=1, message='O valor deve ser maior que zero')
    ])
    descricao = TextAreaField('Descrição (opcional)', validators=[
        Length(max=255, message='Descrição deve ter no máximo 255 caracteres')
    ])
    submit = SubmitField('Realizar Transferência')

    def __init__(self, *args, **kwargs):
        super(TransferenciaBolosForm, self).__init__(*args, **kwargs)
        
        # Carrega usuários ativos para seleção
        usuarios_ativos = [(u.id_usuario, u.nome_usuario) 
                          for u in Usuario.query.filter_by(is_ativo=True).all()]
        
        self.usuario_origem.choices = [(0, 'Selecione o Usuário Origem')] + usuarios_ativos
        self.usuario_destino.choices = [(0, 'Selecione o Usuário Destino')] + usuarios_ativos

    def validate_usuario_origem(self, usuario_origem):
        if usuario_origem.data == 0:
            raise ValidationError('Selecione um Usuário de Origem válido')
        if usuario_origem.data == self.usuario_destino.data:
            raise ValidationError('O usuário de origem não pode ser igual ao de destino')

    def validate_usuario_destino(self, usuario_destino):
        if usuario_destino.data == 0:
            raise ValidationError('Selecione um Usuário de Destino válido')
