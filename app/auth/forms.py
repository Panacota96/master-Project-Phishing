from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
import re

from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class CSVUploadForm(FlaskForm):
    csv_file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only'),
    ])
    submit = SubmitField('Import Users')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')],
    )
    submit = SubmitField('Update Password')

    def validate_new_password(self, field):
        password = field.data or ''
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters.')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must include a lowercase letter.')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must include an uppercase letter.')
        if not re.search(r'\d', password):
            raise ValidationError('Password must include a number.')
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError('Password must include a symbol.')
