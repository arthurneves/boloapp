from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, SubmitField
from wtforms.validators import Optional
from app.models.usuario import Usuario

class LogFiltroForm(FlaskForm):
    usuario_autor = SelectField('Usuário Autor', coerce=int, validators=[Optional()])
    usuario_afetado = SelectField('Usuário Afetado', coerce=int, validators=[Optional()])
    acao = SelectField('Ação', choices=[
        ('', 'Todas'),
        ('Criação', 'Criação'),
        ('Edição', 'Edição'),
        ('Desativação', 'Desativação')
    ], validators=[Optional()])
    data_inicio = DateField('Data Início', validators=[Optional()])
    data_fim = DateField('Data Fim', validators=[Optional()])
    submit = SubmitField('Filtrar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate usuario choices dynamically
        usuarios = Usuario.query.all()
        self.usuario_autor.choices = [(0, 'Todos')] + [(u.id_usuario, u.nome_usuario) for u in usuarios]
        self.usuario_afetado.choices = [(0, 'Todos')] + [(u.id_usuario, u.nome_usuario) for u in usuarios]
