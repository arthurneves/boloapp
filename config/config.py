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

    # Cache Configuration
    CACHE_TYPE = 'RedisCache'
    #CACHE_TYPE = 'SimpleCache'
    CACHE_REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    CACHE_REDIS_PORT = os.getenv('REDIS_PORT', 6379)
    CACHE_REDIS_DB = os.getenv('CACHE_REDIS_DB', 0)
    CACHE_DEFAULT_TIMEOUT = 36000  # 10 horas
