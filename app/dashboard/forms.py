from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo

from app.validators import validate_password_strength


class AdminSetPasswordForm(FlaskForm):
    """Admin form to set a new password for any user.

    Does NOT require the current password — admin privilege bypasses that
    check, matching the behaviour of the existing CSV bulk-import flow.
    Password strength rules are enforced by the shared
    ``validate_password_strength`` validator in ``app/validators.py``.
    """

    new_password = PasswordField('New Password', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')],
    )
    submit = SubmitField('Set Password')
