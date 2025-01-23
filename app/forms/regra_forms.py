from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import DataRequired

class RegraForm(FlaskForm):
    conteudo_regras = TextAreaField('Conteúdo das Regras', validators=[DataRequired()])
