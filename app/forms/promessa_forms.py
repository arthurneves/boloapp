from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_login import current_user
from app.models.promessa import Promessa
from app.models.usuario import Usuario


class PromessaForm(FlaskForm):
    titulo_promessa = StringField('Título da Promessa', validators=[
        DataRequired(message='Título da promessa é obrigatório'),
        Length(min=3, max=100, message='Título deve ter entre 3 e 100 caracteres')
    ])
    descricao_promessa = TextAreaField('Descrição da Promessa', validators=[
        Length(max=255, message='Descrição não pode exceder 255 caracteres')
    ])
    is_ativo = BooleanField('Promessa Ativa', default=True)

    id_usuario = SelectField('Usuário', coerce=int, validators=[DataRequired(message='Selecione um Usuário')])

    submit = SubmitField('Salvar Promessa')

    def __init__(self, promessa_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Carrega usuários ativos para seleção
        self.id_usuario.choices = [(0, 'Selecione um Usuário')] + [
            (usuario.id_usuario, usuario.nome_usuario) 
            for usuario in Usuario.query.filter_by(is_ativo=True).all()
        ]

        self.promessa_id = promessa_id

    def validate_titulo_promessa(self, titulo_promessa):
        # Verifica se já existe uma promessa com o mesmo título para o usuário atual
        query = Promessa.query.filter_by(
            titulo_promessa=titulo_promessa.data, 
            id_usuario=current_user.id_usuario
        )
        
        # Se estiver editando, exclui a promessa atual da verificação
        if self.promessa_id:
            query = query.filter(Promessa.id_promessa != self.promessa_id)
        
        existing_promessa = query.first()
        
        if existing_promessa:
            raise ValidationError('Você já tem uma promessa com este título')
        
    def validate_id_usuario(self, id_usuario):
        if id_usuario.data == 0:
            raise ValidationError('Selecione um Usuário válido')
    
