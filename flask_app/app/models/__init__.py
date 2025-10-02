"""
Models module for Flask app
Contiene tutti i modelli SQLAlchemy interni
"""

from .book import Book
from .page import Page  
from .card import Card
from .asset import Asset

# Re-export per uso nell'app
__all__ = ['Book', 'Page', 'Card', 'Asset']