from flask import Blueprint

bp = Blueprint('inspector', __name__, url_prefix='/inspector')

from app.inspector import routes  # noqa: E402, F401

# All inspector endpoints are JSON API routes protected by @login_required.
# CSRF exemption is applied here so fetch() calls from the SPA don't need
# to embed a CSRF token in the request body or headers.
from app import csrf
csrf.exempt(bp)
