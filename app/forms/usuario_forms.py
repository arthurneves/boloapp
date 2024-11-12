from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models.usuario import Usuario

class RegistroUsuarioForm(FlaskForm):
    nome_usuario = StringField('Nome', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ])
    email_usuario = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=6, message='Senha deve ter no mínimo 6 caracteres')
    ])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('senha', message='Senhas não conferem')
    ])
    is_ativo = BooleanField('Usuário Ativo', default=True)
    is_administrador = BooleanField('Administrador')
    submit = SubmitField('Criar Usuário')

    def validate_email_usuario(self, email_usuario):
        usuario = Usuario.query.filter_by(email_usuario=email_usuario.data).first()
        if usuario:
            raise ValidationError('Este email já está cadastrado')

class LoginForm(FlaskForm):
    email_usuario = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória')
    ])
    submit = SubmitField('Entrar')

class EdicaoUsuarioForm(FlaskForm):
    nome_usuario = StringField('Nome', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ])
    email_usuario = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    is_ativo = BooleanField('Usuário Ativo')
    is_administrador = BooleanField('Administrador')
    submit = SubmitField('Atualizar Usuário')

    def __init__(self, usuario_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario_id = usuario_id

    def validate_email_usuario(self, email_usuario):
        usuario = Usuario.query.filter_by(email_usuario=email_usuario.data).first()
        if usuario and usuario.id_usuario != self.usuario_id:
            raise ValidationError('Este email já está cadastrado')
