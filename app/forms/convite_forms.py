from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, EqualTo
from app.models.usuario import Usuario
from app.models.squad import Squad

class CriarConviteForm(FlaskForm):
    submit = SubmitField('Gerar Convite')

class CadastrarUsuarioConviteForm(FlaskForm):

    nome_usuario = StringField('Nome', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ])

    login_usuario = StringField('Login', validators=[
        DataRequired(message='Login é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ])

    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=6, message='Senha deve ter no mínimo 6 caracteres')
    ])

    confirmar_senha = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('senha', message='Senhas não conferem')
    ])

    id_squad = SelectField('Squad', coerce=int, validators=[DataRequired(message='Selecione um Squad')])

    submit = SubmitField('Criar Usuário')

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Carrega squads ativos para seleção
        self.id_squad.choices = [(0, 'Selecione um Squad')] + [
            (squad.id_squad, squad.titulo_squad) 
            for squad in Squad.query.filter_by(is_ativo=True).all()
        ]

    def validate_login_usuario(self, login_usuario):
        usuario = Usuario.query.filter_by(login_usuario=login_usuario.data).first()
        if usuario:
            raise ValidationError('Este login já está cadastrado')

    def validate_id_squad(self, id_squad):
        if id_squad.data == 0:
            raise ValidationError('Selecione um Squad válido')
