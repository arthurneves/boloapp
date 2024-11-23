from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, SubmitField
from wtforms.validators import Optional
from app.models.usuario import Usuario

class LogFiltroForm(FlaskForm):
    usuario_autor = SelectField('Usuário Autor', coerce=int, validators=[Optional()])
    id_registro_afetado = SelectField('ID Registro Afetado', coerce=int, validators=[Optional()])
    tipo_entidade = SelectField('Tipo Entidade', choices=[
        ('', 'Todas'),
        ('Usuario', 'Usuario'),
        ('Transacao Pontos', 'TransacaoPontos'),
        ('Categoria', 'Categoria')
    ], validators=[Optional()])
    acao = SelectField('Ação', choices=[
        ('', 'Todas'),
        ('Criação', 'Criação'),
        ('Edição', 'Edição'),
        ('Desativação', 'Desativação')
    ], validators=[Optional()])
    data_inicio = DateField('Data Início', format='%d-%m-%Y', validators=[Optional()])
    data_fim = DateField('Data Fim', format='%d-%m-%Y', validators=[Optional()])
    submit = SubmitField('Filtrar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate usuario choices dynamically
        usuarios = Usuario.query.all()
        self.usuario_autor.choices = [(0, 'Todos')] + [(u.id_usuario, u.nome_usuario) for u in usuarios]
