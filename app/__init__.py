from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from config.config import Config
db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models.usuario import Usuario
        return Usuario.query.get(int(user_id))

    # Create tables
    with app.app_context():
        db.create_all()

    # Import and register blueprints
    from .controllers import main_bp
    from .services.notification_service import NotificationService

    app.register_blueprint(main_bp)
    
    # Initialize notification service
    NotificationService.init_app(app)

    return app
