from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
import re

from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError


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


def _validate_password_strength(form, field):
    """Shared password-strength validator used by registration form."""
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


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    class_name = StringField('Class', validators=[DataRequired(), Length(max=64)])
    academic_year = StringField('Academic Year', validators=[DataRequired(), Length(max=16)])
    major = StringField('Major', validators=[DataRequired(), Length(max=64)])
    facility = StringField('Facility / Campus', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), _validate_password_strength])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')],
    )
    submit = SubmitField('Create Account')


class CohortQRForm(FlaskForm):
    """Admin form to generate a generic registration QR code."""
    submit = SubmitField('Generate QR Code')
