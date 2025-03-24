from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeLocalField, BooleanField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.notification import PublicoAlvo
from app.models.usuario import Usuario
from app.models.squad import Squad
from datetime import datetime

class NotificationForm(FlaskForm):
    titulo_notificacao = StringField('Título', validators=[
        DataRequired(message='O título é obrigatório'),
        Length(min=3, max=100, message='O título deve ter entre 3 e 100 caracteres')
    ])
    
    corpo_notificacao = TextAreaField('Mensagem', validators=[
        DataRequired(message='A mensagem é obrigatória'),
        Length(min=5, max=1000, message='A mensagem deve ter entre 5 e 1000 caracteres')
    ])
    
    publico_alvo = SelectField('Público-alvo', choices=[
        (PublicoAlvo.TODOS.value, 'Todos os usuários'),
        (PublicoAlvo.USUARIO_ESPECIFICO.value, 'Usuário específico'),
        (PublicoAlvo.SQUAD.value, 'Squad')
    ], validators=[DataRequired(message='O público-alvo é obrigatório')])
    
    id_usuario_destino = SelectField('Usuário', coerce=int, validators=[Optional()])
    id_squad_destino = SelectField('Squad', coerce=int, validators=[Optional()])
    
    agendamento = DateTimeLocalField('Agendamento (opcional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    
    is_ativo = BooleanField('Ativo', default=True)
    
    submit = SubmitField('Salvar')
    
    def __init__(self, *args, **kwargs):
        super(NotificationForm, self).__init__(*args, **kwargs)
        # Preencher as opções de usuários e squads
        self.id_usuario_destino.choices = [(u.id_usuario, u.nome_usuario) 
                                          for u in Usuario.query.filter_by(is_ativo=True).order_by(Usuario.nome_usuario).all()]
        self.id_squad_destino.choices = [(s.id_squad, s.titulo_squad) 
                                        for s in Squad.query.filter_by(is_ativo=True).order_by(Squad.titulo_squad).all()]
    
    def validate_agendamento(self, field):
        if field.data and field.data < datetime.now():
            raise ValidationError('O agendamento deve ser para um momento futuro')
    
    def validate(self, extra_validators=None):
        if not super(NotificationForm, self).validate(extra_validators=extra_validators):
            return False
        
        # Validações adicionais baseadas no público-alvo
        if self.publico_alvo.data == PublicoAlvo.USUARIO_ESPECIFICO.value and not self.id_usuario_destino.data:
            self.id_usuario_destino.errors.append('Selecione um usuário para enviar a notificação')
            return False
        
        if self.publico_alvo.data == PublicoAlvo.SQUAD.value and not self.id_squad_destino.data:
            self.id_squad_destino.errors.append('Selecione um squad para enviar a notificação')
            return False
        
        return True

class NotificationFilterForm(FlaskForm):
    data_inicio = DateTimeLocalField('Data de início', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    data_fim = DateTimeLocalField('Data de fim', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    status_envio = SelectField('Status', choices=[
        ('', 'Todos'),
        ('pendente', 'Pendente'),
        ('enviado', 'Enviado'),
        ('falha', 'Falha')
    ], validators=[Optional()])
    
    submit = SubmitField('Filtrar')
    
    def validate(self, extra_validators=None):
        if not super(NotificationFilterForm, self).validate(extra_validators=extra_validators):
            return False
        
        if self.data_inicio.data and self.data_fim.data and self.data_inicio.data > self.data_fim.data:
            self.data_inicio.errors.append('A data de início deve ser anterior à data de fim')
            return False
        
        return True
