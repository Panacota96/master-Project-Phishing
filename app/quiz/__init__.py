from flask import Blueprint

bp = Blueprint('quiz', __name__, url_prefix='/quiz')

from app.quiz import routes  # noqa: E402, F401
