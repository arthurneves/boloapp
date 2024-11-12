from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config.config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models.usuario import Usuario
        return Usuario.query.get(int(user_id))

    # Create tables
    with app.app_context():
        from .models.usuario import Usuario
        db.create_all()

    # Import and register blueprints
    from .controllers import main_bp
    app.register_blueprint(main_bp)

    return app
