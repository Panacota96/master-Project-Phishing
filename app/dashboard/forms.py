import re

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError


class AdminSetPasswordForm(FlaskForm):
    """Admin form to set a new password for any user.

    Does NOT require the current password — admin privilege bypasses that
    check, matching the behaviour of the existing CSV bulk-import flow.
    Password strength rules mirror those in ``app/auth/forms.py``.
    """

    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')],
    )
    submit = SubmitField('Set Password')

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
