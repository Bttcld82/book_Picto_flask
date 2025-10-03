#!/usr/bin/env python3
"""
Script per creare dati di test per l'applicazione AAC
"""

from app import create_app
from app.db import get_db, close_db
from app.models import Book, Page, Card, Asset

def create_test_data():
    """Crea alcuni dati di test"""
    app = create_app()
    
    with app.app_context():
        db = get_db()
        try:
            # Controlla se ci sono già libri
            existing_books = db.query(Book).count()
            if existing_books > 0:
                print(f"Esistono già {existing_books} libri nel database")
                return
            
            # Crea libro di test
            test_book = Book(
                title="Il Mio Primo Libro AAC",
                locale="it-IT"
            )
            db.add(test_book)
            db.commit()
            
            # Crea una pagina di test
            test_page = Page(
                book_id=test_book.id,
                title="Pagina Principale",
                grid_cols=3,
                grid_rows=3,
                order=1
            )
            db.add(test_page)
            db.commit()
            
            # Imposta come home page
            test_book.home_page_id = test_page.id
            db.commit()
            
            # Crea alcune carte di test
            cards_data = [
                {"label": "Ciao", "slot_row": 0, "slot_col": 0},
                {"label": "Casa", "slot_row": 0, "slot_col": 1},
                {"label": "Mangiare", "slot_row": 0, "slot_col": 2},
                {"label": "Bere", "slot_row": 1, "slot_col": 0},
                {"label": "Dormire", "slot_row": 1, "slot_col": 1},
                {"label": "Giocare", "slot_row": 1, "slot_col": 2},
            ]
            
            for card_data in cards_data:
                card = Card(
                    page_id=test_page.id,
                    label=card_data["label"],
                    slot_row=card_data["slot_row"],
                    slot_col=card_data["slot_col"]
                )
                db.add(card)
            
            db.commit()
            print(f"✅ Creati dati di test:")
            print(f"   - Libro: {test_book.title} (ID: {test_book.id})")
            print(f"   - Pagina: {test_page.title} (ID: {test_page.id})")
            print(f"   - {len(cards_data)} carte AAC")
            
        except Exception as e:
            print(f"❌ Errore durante la creazione: {e}")
            db.rollback()
        finally:
            close_db(db)

if __name__ == "__main__":
    create_test_data()