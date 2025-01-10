import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'desenvolvimento_boloapp_arthur_neves')
    
    # MySQL Database Configuration
    SQLALCHEMY_DATABASE_URI = (
        f"mysql://{os.getenv('DB_USER', 'admin')}:"
        f"{os.getenv('DB_PASSWORD', '')}@"
        f"{os.getenv('DB_HOST', 'localhost')}/"
        f"{os.getenv('DB_NAME', 'boloapp')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
