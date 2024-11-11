from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config.config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Create tables
    with app.app_context():
        from .models.usuario import Usuario
        db.create_all()

    # Import and register blueprints
    from .controllers import main_bp
    app.register_blueprint(main_bp)

    return app
