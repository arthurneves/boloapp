from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, SubmitField
from wtforms.validators import Optional
from app.models.usuario import Usuario

class LogFiltroForm(FlaskForm):
    usuario_autor = SelectField('Usuário Autor', coerce=int, validators=[Optional()])
    usuario_afetado = SelectField('Usuário Afetado', coerce=int, validators=[Optional()])
    id_registro_afetado = SelectField('ID Registro Afetado', coerce=int, validators=[Optional()])
    tipo_entidade = SelectField('Tipo Entidade', choices=[
                                                            ('', 'Todas'),
                                                            ('usuario', 'Usuario'),
                                                            ('transacao_bolos', 'Transação de Bolos'),
                                                            ('promessa', 'Promessa'),
                                                            ('votacao', 'Votação'),
                                                            ('categoria', 'Categoria'),
                                                            ('squad', 'Squad'),
                                                            ('convite', 'Convite')
                                                        ], validators=[Optional()])
    acao = SelectField('Ação', choices=[
                                            ('', 'Todas'),
                                            ('criar', 'Criação'),
                                            ('editar', 'Edição'),
                                            ('desativar', 'Desativação'),
                                            ('reativar', 'Reativação')
                                        ], validators=[Optional()])
    data_inicio = DateField('Data Início', format='%d-%m-%Y', validators=[Optional()])
    data_fim = DateField('Data Fim', format='%d-%m-%Y', validators=[Optional()])
    submit = SubmitField('Filtrar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        usuarios = Usuario.query.all()
        self.usuario_autor.choices = [(0, 'Todos')] + [(u.id_usuario, u.nome_usuario) for u in usuarios]
        self.usuario_afetado.choices = [(0, 'Todos')] + [(u.id_usuario, u.nome_usuario) for u in usuarios]
