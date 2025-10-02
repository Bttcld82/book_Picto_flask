"""
Schemas module for Flask app
Importa tutti gli schema Pydantic dal backend FastAPI esistente
"""

import os
import sys

# Aggiungi il path al backend per accedere agli schema esistenti
BACKEND_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend')
sys.path.insert(0, BACKEND_PATH)

# Import tutti gli schema dal backend esistente
try:
    from app.schemas.book import BookCreate, BookUpdate, BookRead
    from app.schemas.page import PageCreate, PageUpdate, PageRead
    from app.schemas.card import CardCreate, CardUpdate, CardRead
    from app.schemas.asset import AssetCreate, AssetUpdate, AssetRead
except ImportError as e:
    print(f"Errore import schema dal backend: {e}")
    print("Schema Pydantic non critici per Flask, continuo senza...")
    # Definiamo fallback vuoti se necessario
    BookCreate = BookUpdate = BookRead = None
    PageCreate = PageUpdate = PageRead = None
    CardCreate = CardUpdate = CardRead = None
    AssetCreate = AssetUpdate = AssetRead = None

# Re-export per uso nel Flask app (principalmente per validazione)
__all__ = [
    'BookCreate', 'BookUpdate', 'BookRead',
    'PageCreate', 'PageUpdate', 'PageRead', 
    'CardCreate', 'CardUpdate', 'CardRead',
    'AssetCreate', 'AssetUpdate', 'AssetRead'
]