from flask import Blueprint, render_template, request
from ..db import get_db, close_db
from ..models import Book

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage - lista dei libri con ricerca"""
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
        
        return render_template('index.html', 
                             books=books, 
                             search_query=search_query,
                             total_books=len(books))
    finally:
        close_db(db)