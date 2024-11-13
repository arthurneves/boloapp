from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models.categoria import Categoria

class CategoriaForm(FlaskForm):
    titulo_categoria = StringField('Título da Categoria', validators=[
        DataRequired(message='Título da categoria é obrigatório'),
        Length(min=2, max=100, message='Título deve ter entre 2 e 100 caracteres')
    ])
    descricao_categoria = TextAreaField('Descrição', validators=[
        Length(max=500, message='Descrição deve ter no máximo 500 caracteres')
    ])
    is_ativo = BooleanField('Categoria Ativa', default=True)
    submit = SubmitField('Salvar Categoria')

    def __init__(self, categoria_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.categoria_id = categoria_id

    def validate_titulo_categoria(self, titulo_categoria):
        # Verifica se já existe uma categoria com o mesmo título
        query = Categoria.query.filter_by(titulo_categoria=titulo_categoria.data)
        
        # Se estiver editando, exclui a categoria atual da verificação
        if self.categoria_id:
            query = query.filter(Categoria.id_categoria != self.categoria_id)
        
        existing_categoria = query.first()
        
        if existing_categoria:
            raise ValidationError('Já existe uma categoria com este título')
