import os

from asgiref.wsgi import WsgiToAsgi
from mangum import Mangum

# Patch boto3 with X-Ray SDK when running inside Lambda (no-op locally)
if os.environ.get('AWS_EXECUTION_ENV'):
    from aws_xray_sdk.core import patch_all
    patch_all()

from app import create_app

app = create_app()
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app, lifespan="off")
