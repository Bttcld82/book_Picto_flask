from flask import Blueprint, render_template, request
from ..db import get_db, close_db
from ..models import Book, Page, Card

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage - lista dei libri con ricerca e statistiche"""
    db = get_db()
    try:
        # Parametri di ricerca
        search_query = request.args.get('q', '').strip()
        
        # Query base
        books_query = db.query(Book)
        
        # Filtro per ricerca
        if search_query:
            books_query = books_query.filter(
                Book.title.ilike(f'%{search_query}%')
            )
        
        books = books_query.all()
        
        # Carica le pagine per ogni libro per mostrare le statistiche
        for book in books:
            book.pages = db.query(Page).filter(Page.book_id == book.id).all()
            
            # Conta le carte totali per ogni libro
            total_cards = 0
            for page in book.pages:
                cards_count = db.query(Card).filter(Card.page_id == page.id).count()
                total_cards += cards_count
            book.total_cards = total_cards
        
        return render_template('books/list.html', 
                             books=books, 
                             search_query=search_query,
                             total_books=len(books))
    finally:
        close_db(db)