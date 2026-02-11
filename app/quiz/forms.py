from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField


class QuestionForm(FlaskForm):
    answer = RadioField('Your Answer', coerce=int)
    submit = SubmitField('Submit Answer')
