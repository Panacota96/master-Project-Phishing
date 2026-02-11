from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)

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

    with app.app_context():
        db.create_all()

    return app
