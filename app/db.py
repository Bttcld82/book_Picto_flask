"""
Database module for Flask app
Setup database SQLAlchemy completo e autonomo
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import config

# Configura engine database
engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False} if config.SQLALCHEMY_DATABASE_URI.startswith("sqlite") else {},
    echo=config.DEBUG  # Log SQL queries in development
)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    """Base class per tutti i modelli SQLAlchemy"""
    pass

def init_db():
    """Inizializza il database creando tutte le tabelle"""
    # Import tutti i modelli per assicurarsi che siano registrati
    from .models import book, page, card, asset  # noqa
    
    # Crea tutte le tabelle
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Helper per ottenere una sessione database
    Da usare nei route Flask
    """
    db = SessionLocal()
    return db

def get_db_session():
    """
    Alias per get_db() per compatibilità
    """
    return get_db()

def close_db(db):
    """
    Helper per chiudere la sessione database
    """
    if db:
        db.close()

# Context manager per uso con 'with'
class DatabaseSession:
    """Context manager per gestione automatica sessioni database"""
    
    def __enter__(self):
        self.db = get_db()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.db.rollback()
        close_db(self.db)