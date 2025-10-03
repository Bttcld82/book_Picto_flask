from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db, close_db
from ..models import Book, Page, Card, Asset

books_bp = Blueprint('books', __name__)

@books_bp.route('/')
def list_books():
    """Lista di tutti i libri con statistiche"""
    db = get_db()
    try:
        books = db.query(Book).all()
        
        # Carica le pagine per ogni libro per mostrare le statistiche
        for book in books:
            book.pages = db.query(Page).filter(Page.book_id == book.id).all()
            
            # Conta le carte totali per ogni libro
            total_cards = 0
            for page in book.pages:
                cards_count = db.query(Card).filter(Card.page_id == page.id).count()
                total_cards += cards_count
            book.total_cards = total_cards
        
        return render_template('books/list.html', books=books)
    finally:
        close_db(db)

@books_bp.route('/<int:book_id>')
def view_book(book_id):
    """Dettaglio di un libro specifico"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        # Ottieni le pagine del libro (se il modello ha questa relazione)
        pages = getattr(book, 'pages', [])
        
        return render_template('books/detail.html', book=book, pages=pages)
    finally:
        close_db(db)

@books_bp.route('/new', methods=['GET', 'POST'])
def create_book():
    """Crea un nuovo libro"""
    if request.method == 'POST':
        db = get_db()
        try:
            title = request.form.get('title', '').strip()
            locale = request.form.get('locale', 'it-IT')
            
            if not title:
                flash('Il titolo è obbligatorio', 'error')
                return render_template('books/new.html')
            
            # Crea nuovo libro
            new_book = Book(title=title, locale=locale)
            db.add(new_book)
            db.commit()
            db.refresh(new_book)
            
            flash(f'Libro "{title}" creato con successo!', 'success')
            return redirect(url_for('books.view_book', book_id=new_book.id))
            
        except Exception as e:
            db.rollback()
            flash(f'Errore nella creazione del libro: {str(e)}', 'error')
            return render_template('books/new.html')
        finally:
            close_db(db)
    
    return render_template('books/new.html')

@books_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
def edit_book(book_id):
    """Modifica un libro esistente"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            locale = request.form.get('locale', book.locale)
            
            if not title:
                flash('Il titolo è obbligatorio', 'error')
                return render_template('books/edit.html', book=book)
            
            # Aggiorna libro
            book.title = title
            book.locale = locale
            db.commit()
            
            flash(f'Libro "{title}" aggiornato con successo!', 'success')
            return redirect(url_for('books.view_book', book_id=book.id))
        
        return render_template('books/edit.html', book=book)
        
    finally:
        close_db(db)

@books_bp.route('/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    """Elimina un libro"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        book_title = book.title
        db.delete(book)
        db.commit()
        
        flash(f'Libro "{book_title}" eliminato con successo!', 'success')
        return redirect(url_for('books.list_books'))
        
    except Exception as e:
        db.rollback()
        flash(f'Errore nell\'eliminazione del libro: {str(e)}', 'error')
        return redirect(url_for('books.view_book', book_id=book_id))
    finally:
        close_db(db)

@books_bp.route('/<int:book_id>/runtime')
def runtime_book(book_id):
    """Modalità runtime del libro AAC - visualizzazione end-user"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        # Trova la home page o la prima pagina
        home_page = None
        if book.home_page_id:
            home_page = db.query(Page).filter(
                Page.id == book.home_page_id,
                Page.book_id == book_id
            ).first()
        
        if not home_page:
            # Prendi la prima pagina disponibile
            home_page = db.query(Page).filter(
                Page.book_id == book_id
            ).order_by(Page.order.asc()).first()
        
        if not home_page:
            flash('Questo libro non ha ancora pagine. Creane una prima di aprirlo.', 'warning')
            return redirect(url_for('books.view_book', book_id=book_id))
        
        # Ottieni tutte le pagine del libro per la navigazione
        all_pages = db.query(Page).filter(
            Page.book_id == book_id
        ).order_by(Page.order.asc()).all()
        
        # Ottieni le carte della home page con le immagini
        cards = db.query(Card).filter(
            Card.page_id == home_page.id
        ).all()
        
        # Carica le immagini e pagine target associate alle carte
        for card in cards:
            if card.image_id:
                card.image = db.query(Asset).filter(
                    Asset.id == card.image_id
                ).first()
            if card.target_page_id:
                card.target_page = db.query(Page).filter(
                    Page.id == card.target_page_id,
                    Page.book_id == book_id
                ).first()
        
        return render_template('books/runtime_simple.html', 
                             book=book, 
                             current_page=home_page,
                             all_pages=all_pages,
                             cards=cards)
    finally:
        close_db(db)

@books_bp.route('/<int:book_id>/runtime/<int:page_id>')
def runtime_page(book_id, page_id):
    """Visualizza una pagina specifica in modalità runtime"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        page = db.query(Page).filter(
            Page.id == page_id,
            Page.book_id == book_id
        ).first()
        
        if not page:
            flash('Pagina non trovata', 'error')
            return redirect(url_for('books.runtime_book', book_id=book_id))
        
        # Ottieni tutte le pagine del libro per la navigazione
        all_pages = db.query(Page).filter(
            Page.book_id == book_id
        ).order_by(Page.order.asc()).all()
        
        # Ottieni le carte della pagina con le immagini
        cards = db.query(Card).filter(
            Card.page_id == page.id
        ).all()
        
        # Carica le immagini e pagine target associate alle carte
        for card in cards:
            if card.image_id:
                card.image = db.query(Asset).filter(
                    Asset.id == card.image_id
                ).first()
            if card.target_page_id:
                card.target_page = db.query(Page).filter(
                    Page.id == card.target_page_id,
                    Page.book_id == book_id
                ).first()
        
        return render_template('books/runtime_simple.html', 
                             book=book, 
                             current_page=page,
                             all_pages=all_pages,
                             cards=cards)
    finally:
        close_db(db)