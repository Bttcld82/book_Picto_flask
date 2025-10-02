from flask import Flask
from flask_cors import CORS
from .config import config

def create_app():
    app = Flask(__name__)
    
    # Configurazione da config.py
    app.config.from_object(config)
    
    # CORS per development
    CORS(app, origins=config.CORS_ORIGINS)
    
    # Inizializza database
    with app.app_context():
        from .db import init_db
        init_db()
    
    # Registra blueprint
    from .routes.books import books_bp
    from .routes.main import main_bp
    from .routes.pages import pages_bp
    from .routes.cards import cards_bp
    from .routes.assets import assets_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(pages_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(assets_bp)
    
    return app