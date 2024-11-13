from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models.squad import Squad

class SquadForm(FlaskForm):
    titulo_squad = StringField('Título do Squad', validators=[
        DataRequired(message='Título do squad é obrigatório'),
        Length(min=2, max=100, message='Título deve ter entre 2 e 100 caracteres')
    ])
    is_ativo = BooleanField('Squad Ativo', default=True)
    submit = SubmitField('Salvar Squad')

    def __init__(self, squad_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.squad_id = squad_id

    def validate_titulo_squad(self, titulo_squad):
        # Verifica se já existe um squad com o mesmo título
        query = Squad.query.filter_by(titulo_squad=titulo_squad.data)
        
        # Se estiver editando, exclui o squad atual da verificação
        if self.squad_id:
            query = query.filter(Squad.id_squad != self.squad_id)
        
        existing_squad = query.first()
        
        if existing_squad:
            raise ValidationError('Já existe um squad com este título')
