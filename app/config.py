"""
Configuration module for Flask app
Configurazione semplificata per l'applicazione Flask
"""

import os
from pathlib import Path

class Config:
    """Configurazione base dell'applicazione Flask"""
    
    # App settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-flask-aac-builder')
    APP_ENV = os.environ.get('APP_ENV', 'development')
    DEBUG = APP_ENV == 'development'
    
    # Database settings
    BASE_DIR = Path(__file__).parent.parent
    DATABASE_PATH = BASE_DIR / 'data.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DATABASE_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    STATIC_DIR = BASE_DIR / 'app' / 'static'
    MEDIA_DIR = STATIC_DIR / 'media'
    UPLOAD_FOLDER = str(MEDIA_DIR)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    
    # CORS settings (per development)
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000']
    
    def __init__(self):
        # Crea cartelle necessarie
        self.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        self.STATIC_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def allowed_file(filename):
        """Verifica se il file è permesso per upload"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Istanza globale della configurazione
config = Config()