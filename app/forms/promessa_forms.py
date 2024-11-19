from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, Regexp

class PromessaForm(FlaskForm):
    id_promessa = HiddenField('ID da Promessa')
    
    titulo_promessa = StringField('Título da Promessa', validators=[
        DataRequired(message='O título da promessa é obrigatório'),
        Length(min=3, max=255, message='O título deve ter entre 3 e 255 caracteres'),
        Regexp(r'^[a-zA-Z0-9\s]+$', message='O título deve conter apenas letras, números e espaços')
    ])
    
    descricao_promessa = TextAreaField('Descrição da Promessa', validators=[
        Optional(),
        Length(max=1000, message='A descrição não pode exceder 1000 caracteres')
    ])
    
    is_ativo = BooleanField('Ativo', default=True)
    
    submit = SubmitField('Salvar Promessa')

    def validate(self, extra_validators=None):
        """
        Método de validação personalizado para limpeza de dados
        """
        # Chama a validação padrão
        if not super().validate(extra_validators):
            return False
        
        # Limpa espaços extras dos campos
        if self.titulo_promessa.data:
            self.titulo_promessa.data = self.titulo_promessa.data.strip()
        
        if self.descricao_promessa.data:
            self.descricao_promessa.data = self.descricao_promessa.data.strip()
        
        return True
