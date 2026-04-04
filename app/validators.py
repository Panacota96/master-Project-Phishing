"""Shared WTForms validators used across multiple blueprints."""

import re

from wtforms.validators import ValidationError


def validate_password_strength(form, field):
    """WTForms validator that enforces the application password-strength policy.

    Rules (must all pass):
    - At least 8 characters
    - At least one lowercase letter
    - At least one uppercase letter
    - At least one digit
    - At least one non-alphanumeric character (symbol)
    """
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
