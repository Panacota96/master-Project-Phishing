from flask import Blueprint

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

from app.dashboard import routes  # noqa: E402, F401
