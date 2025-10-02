from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from ..db import get_db, close_db
from ..models import Book, Page, Card

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def list_pages(book_id):
    """Lista tutte le pagine di un libro"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        pages = db.query(Page).filter(Page.book_id == book_id).order_by(Page.order, Page.id).all()
        
        return render_template('pages/list.html', book=book, pages=pages)
    finally:
        close_db(db)

@pages_bp.route('/<int:page_id>')
def view_page(book_id, page_id):
    """Visualizza una pagina specifica con le sue carte"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        page = db.query(Page).filter(Page.id == page_id, Page.book_id == book_id).first()
        
        if not book or not page:
            flash('Pagina non trovata', 'error')
            return redirect(url_for('books.view_book', book_id=book_id))
        
        # Ottieni tutte le carte della pagina
        cards = db.query(Card).filter(Card.page_id == page_id).all()
        
        # Crea griglia per visualizzazione
        grid = [[None for _ in range(page.grid_cols)] for _ in range(page.grid_rows)]
        for card in cards:
            if 0 <= card.slot_row < page.grid_rows and 0 <= card.slot_col < page.grid_cols:
                grid[card.slot_row][card.slot_col] = card
        
        return render_template('pages/detail.html', book=book, page=page, cards=cards, grid=grid)
    finally:
        close_db(db)

@pages_bp.route('/new', methods=['GET', 'POST'])
def create_page(book_id):
    """Crea una nuova pagina"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            grid_cols = int(request.form.get('grid_cols', 3))
            grid_rows = int(request.form.get('grid_rows', 3))
            
            if not title:
                flash('Il titolo è obbligatorio', 'error')
                return render_template('pages/new.html', book=book)
            
            # Calcola il prossimo numero d'ordine
            max_order = db.query(Page).filter(Page.book_id == book_id).count()
            
            # Crea nuova pagina
            new_page = Page(
                book_id=book_id,
                title=title,
                grid_cols=max(1, min(grid_cols, 10)),  # Limita tra 1 e 10
                grid_rows=max(1, min(grid_rows, 10)),  # Limita tra 1 e 10
                order=max_order
            )
            
            db.add(new_page)
            db.commit()
            db.refresh(new_page)
            
            flash(f'Pagina "{title}" creata con successo!', 'success')
            return redirect(url_for('pages.view_page', book_id=book_id, page_id=new_page.id))
            
        return render_template('pages/new.html', book=book)
        
    except Exception as e:
        if db:
            db.rollback()
        flash(f'Errore nella creazione della pagina: {str(e)}', 'error')
        return redirect(url_for('books.view_book', book_id=book_id))
    finally:
        close_db(db)

@pages_bp.route('/<int:page_id>/edit', methods=['GET', 'POST'])
def edit_page(book_id, page_id):
    """Modifica una pagina esistente"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        page = db.query(Page).filter(Page.id == page_id, Page.book_id == book_id).first()
        
        if not book or not page:
            flash('Pagina non trovata', 'error')
            return redirect(url_for('books.view_book', book_id=book_id))
        
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            grid_cols = int(request.form.get('grid_cols', page.grid_cols))
            grid_rows = int(request.form.get('grid_rows', page.grid_rows))
            order = int(request.form.get('order', page.order))
            
            if not title:
                flash('Il titolo è obbligatorio', 'error')
                return render_template('pages/edit.html', book=book, page=page)
            
            # Aggiorna pagina
            page.title = title
            page.grid_cols = max(1, min(grid_cols, 10))
            page.grid_rows = max(1, min(grid_rows, 10))
            page.order = order
            
            db.commit()
            
            flash(f'Pagina "{title}" aggiornata con successo!', 'success')
            return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
        
        return render_template('pages/edit.html', book=book, page=page)
        
    finally:
        close_db(db)

@pages_bp.route('/<int:page_id>/delete', methods=['POST'])
def delete_page(book_id, page_id):
    """Elimina una pagina"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        page = db.query(Page).filter(Page.id == page_id, Page.book_id == book_id).first()
        
        if not book or not page:
            flash('Pagina non trovata', 'error')
            return redirect(url_for('books.view_book', book_id=book_id))
        
        page_title = page.title
        
        # Controlla se questa è la home page del libro
        if book.home_page_id == page_id:
            book.home_page_id = None
            
        db.delete(page)
        db.commit()
        
        flash(f'Pagina "{page_title}" eliminata con successo!', 'success')
        return redirect(url_for('books.view_book', book_id=book_id))
        
    except Exception as e:
        db.rollback()
        flash(f'Errore nell\'eliminazione della pagina: {str(e)}', 'error')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
    finally:
        close_db(db)

@pages_bp.route('/<int:page_id>/set-home', methods=['POST'])
def set_home_page(book_id, page_id):
    """Imposta una pagina come home page del libro"""
    db = get_db()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        page = db.query(Page).filter(Page.id == page_id, Page.book_id == book_id).first()
        
        if not book or not page:
            flash('Pagina non trovata', 'error')
            return redirect(url_for('books.view_book', book_id=book_id))
        
        book.home_page_id = page_id
        db.commit()
        
        flash(f'Pagina "{page.title}" impostata come home page!', 'success')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
        
    except Exception as e:
        db.rollback()
        flash(f'Errore nell\'impostazione home page: {str(e)}', 'error')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
    finally:
        close_db(db)