from flask import Blueprint

bp = Blueprint('inspector', __name__, url_prefix='/inspector')

from app.inspector import routes  # noqa: E402, F401
