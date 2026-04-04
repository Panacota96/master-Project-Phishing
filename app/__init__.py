import boto3
import redis
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize CSRF protection
    csrf.init_app(app)

    # Initialize DynamoDB resource
    dynamodb_kwargs = {
        'region_name': app.config['AWS_REGION'],
    }
    if app.config.get('DYNAMODB_ENDPOINT'):
        dynamodb_kwargs['endpoint_url'] = app.config['DYNAMODB_ENDPOINT']

    app.dynamodb = boto3.resource('dynamodb', **dynamodb_kwargs)

    # Initialize S3 client
    s3_kwargs = {
        'region_name': app.config['AWS_REGION'],
    }
    if app.config.get('S3_ENDPOINT'):
        s3_kwargs['endpoint_url'] = app.config['S3_ENDPOINT']

    app.s3_client = boto3.client('s3', **s3_kwargs)

    # Initialize SQS client (used by QR self-registration flow)
    app.sqs_client = boto3.client('sqs', region_name=app.config['AWS_REGION'])

    # Initialize SES client (bulk + validation emails)
    app.ses_client = boto3.client('ses', region_name=app.config['AWS_REGION'])

    # Initialize Lambda client (campaign mailer fan-out)
    app.lambda_client = boto3.client('lambda', region_name=app.config['AWS_REGION'])

    # Initialize Redis (ElastiCache) if configured
    redis_endpoint = app.config.get('REDIS_URL') or app.config.get('REDIS_ENDPOINT')
    app.redis_client = None
    if redis_endpoint:
        scheme = 'rediss' if app.config.get('REDIS_USE_TLS') else 'redis'
        if '://' not in redis_endpoint:
            redis_endpoint = f"{scheme}://{redis_endpoint}"
        try:
            app.redis_client = redis.Redis.from_url(redis_endpoint)
        except Exception:
            app.logger.warning('Unable to initialize Redis client; continuing without cache.')

    # Initialize Flask-Login
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(username):
        from app.models import get_user
        return get_user(username)

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.quiz import bp as quiz_bp
    app.register_blueprint(quiz_bp)

    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.inspector import bp as inspector_bp
    app.register_blueprint(inspector_bp)

    @app.route('/')
    def index():
        return redirect(url_for('quiz.quiz_list'))

    return app
