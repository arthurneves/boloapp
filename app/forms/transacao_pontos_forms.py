from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, BooleanField, SubmitField, SelectField, ValidationError
from wtforms.validators import DataRequired, Length, NumberRange
from app.models.categoria import Categoria
from app.models.usuario import Usuario

class TransacaoPontosForm(FlaskForm):
    id_usuario = SelectField('Usuário', coerce=int, validators=[
        DataRequired(message='Selecione um usuário')
    ])
    id_categoria = SelectField('Categoria', coerce=int, validators=[
        DataRequired(message='Selecione uma categoria')
    ])
    pontos_transacao = IntegerField('Pontos', default=1, validators=[
        DataRequired(message='Pontos são obrigatórios')
    ])
    descricao_transacao = TextAreaField('Descrição', validators=[
        Length(max=255, message='Descrição deve ter no máximo 255 caracteres')
    ])
    is_ativo = BooleanField('Transação Ativa', default=True)
    submit = SubmitField('Salvar Transação')

    def __init__(self, *args, **kwargs):

        usuario = kwargs.pop('id_usuario', None)  # Remove 'id_usuario' de kwargs
        super(TransacaoPontosForm, self).__init__(*args, **kwargs)

        if usuario is None:
            # Carrega usuários ativos para seleção
            self.id_usuario.choices = [(0, 'Selecione um Usuário')] + [
                (usuario.id_usuario, usuario.nome_usuario) 
                for usuario in Usuario.query.filter_by(is_ativo=True).all()
            ]
        else:
            self.id_usuario.choices = [
                (usuario.id_usuario, usuario.nome_usuario) 
                for usuario in Usuario.query.filter_by(id_usuario=usuario, is_ativo=True).all()
            ]
        
        # Carrega categorias ativas para seleção
        self.id_categoria.choices = [(0, 'Selecione uma Categoria')] + [
            (categoria.id_categoria, categoria.titulo_categoria) 
            for categoria in Categoria.query.filter_by(is_ativo=True).all()
        ]

    def validate_id_usuario(self, id_usuario):
        if id_usuario.data == 0:
            raise ValidationError('Selecione um Usuário válido')

    def validate_id_categoria(self, id_categoria):
        if id_categoria.data == 0:
            raise ValidationError('Selecione uma Categoria válida')
