"""
Route per la gestione delle Carte AAC
Gestisce il CRUD completo delle carte con grid editor
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.db import get_db, close_db
from app.models.book import Book
from app.models.page import Page
from app.models.card import Card
from app.models.asset import Asset

cards_bp = Blueprint('cards', __name__)


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards')
def list_cards(book_id, page_id):
    """Lista tutte le carte di una pagina specifica"""
    db = get_db()
    try:
        # Verifica esistenza book e page
        book = db.query(Book).filter_by(id=book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        page = db.query(Page).filter_by(id=page_id, book_id=book_id).first()
        if not page:
            flash('Pagina non trovata', 'error')
            return redirect(url_for('pages.list_pages', book_id=book_id))
        
        # Recupera tutte le carte della pagina ordinate per posizione
        cards = db.query(Card).filter_by(page_id=page_id).order_by(Card.slot_row, Card.slot_col).all()
        
        return render_template('cards/list.html', 
                             book=book, 
                             page=page, 
                             cards=cards)
    
    except SQLAlchemyError as e:
        flash(f'Errore database: {str(e)}', 'error')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
    finally:
        close_db(db)


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards/<int:card_id>')
def view_card(book_id, page_id, card_id):
    """Visualizza una carta specifica"""
    db = get_db()
    try:
        # Verifica esistenza e relazioni
        card = db.query(Card).filter_by(
            id=card_id, 
            page_id=page_id
        ).first()
        
        if not card:
            flash('Carta non trovata', 'error')
            return redirect(url_for('cards.list_cards', book_id=book_id, page_id=page_id))
        
        # Carica relazioni
        book = card.page.book
        page = card.page
        
        if book.id != book_id:
            flash('Carta non appartiene al libro specificato', 'error')
            return redirect(url_for('books.list_books'))
        
        return render_template('cards/detail.html',
                             book=book,
                             page=page,
                             card=card)
    
    except SQLAlchemyError as e:
        flash(f'Errore database: {str(e)}', 'error')
        return redirect(url_for('cards.list_cards', book_id=book_id, page_id=page_id))
    finally:
        close_db(db)


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards/new', methods=['GET', 'POST'])
def create_card(book_id, page_id):
    """Crea una nuova carta"""
    db = get_db()
    try:
        # Verifica esistenza book e page
        book = db.query(Book).filter_by(id=book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        page = db.query(Page).filter_by(id=page_id, book_id=book_id).first()
        if not page:
            flash('Pagina non trovata', 'error')
            return redirect(url_for('pages.list_pages', book_id=book_id))
        
        # GET: mostra form di creazione
        if request.method == 'GET':
            # Posizione suggerita (dalla query string o prima libera)
            suggested_x = request.args.get('x', type=int)
            suggested_y = request.args.get('y', type=int)
            
            # Se non specificata, trova prima posizione libera
            if suggested_x is None or suggested_y is None:
                occupied_positions = {(card.slot_col, card.slot_row) for card in page.cards}
                suggested_x, suggested_y = find_free_position(page, occupied_positions)
            
            # Lista asset disponibili per selezione
            assets = db.query(Asset).all()
            
            return render_template('cards/new.html',
                                 book=book,
                                 page=page,
                                 suggested_x=suggested_x,
                                 suggested_y=suggested_y,
                                 assets=assets)
        
        # POST: crea la carta
        text = request.form.get('text', '').strip()
        slot_col = request.form.get('x', type=int)
        slot_row = request.form.get('y', type=int)
        action_type = request.form.get('action_type', 'none')
        
        # Validazioni
        if not text:
            flash('Il testo della carta è obbligatorio', 'error')
            return redirect(request.url)
        
        if slot_col is None or slot_row is None:
            flash('Posizione non valida', 'error')
            return redirect(request.url)
        
        if slot_col < 0 or slot_col >= page.grid_cols or slot_row < 0 or slot_row >= page.grid_rows:
            flash(f'Posizione fuori dalla griglia ({page.grid_cols}×{page.grid_rows})', 'error')
            return redirect(request.url)
        
        # Verifica posizione libera
        existing_card = db.query(Card).filter_by(page_id=page_id, slot_col=slot_col, slot_row=slot_row).first()
        if existing_card:
            flash(f'Posizione ({slot_col}, {slot_row}) già occupata', 'error')
            return redirect(request.url)
        
        # Gestione asset immagine
        image_asset_id = request.form.get('image_asset_id', type=int)
        if image_asset_id:
            asset = db.query(Asset).filter_by(id=image_asset_id).first()
            if not asset:
                flash('Asset selezionato non valido', 'error')
                return redirect(request.url)
        
        # Gestione azione navigazione
        target_page_id = None
        if action_type == 'navigation':
            target_page_id = request.form.get('target_page_id', type=int)
            if target_page_id:
                target_page = db.query(Page).filter_by(id=target_page_id, book_id=book_id).first()
                if not target_page:
                    flash('Pagina di destinazione non valida', 'error')
                    return redirect(request.url)
        
        # Crea nuova carta
        new_card = Card(
            label=text,
            slot_col=slot_col,
            slot_row=slot_row,
            page_id=page_id,
            image_id=image_asset_id,
            target_page_id=target_page_id
        )
        
        db.add(new_card)
        db.commit()
        
        flash(f'Carta "{text}" creata con successo!', 'success')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
    
    except SQLAlchemyError as e:
        db.rollback()
        flash(f'Errore nella creazione della carta: {str(e)}', 'error')
        return redirect(url_for('cards.list_cards', book_id=book_id, page_id=page_id))
    finally:
        close_db(db)


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards/<int:card_id>/edit', methods=['GET', 'POST'])
def edit_card(book_id, page_id, card_id):
    """Modifica una carta esistente"""
    db = get_db()
    try:
        # Verifica esistenza carta
        card = db.query(Card).filter_by(id=card_id, page_id=page_id).first()
        if not card:
            flash('Carta non trovata', 'error')
            return redirect(url_for('cards.list_cards', book_id=book_id, page_id=page_id))
        
        book = card.page.book
        page = card.page
        
        if book.id != book_id:
            flash('Carta non appartiene al libro specificato', 'error')
            return redirect(url_for('books.list_books'))
        
        # GET: mostra form di modifica
        if request.method == 'GET':
            assets = db.query(Asset).order_by(Asset.id.desc()).all()
            pages = db.query(Page).filter_by(book_id=book_id).order_by(Page.order).all()
            
            return render_template('cards/edit.html',
                                 book=book,
                                 page=page,
                                 card=card,
                                 assets=assets,
                                 pages=pages)
        
        # POST: aggiorna la carta
        text = request.form.get('text', '').strip()
        slot_col = request.form.get('x', type=int)
        slot_row = request.form.get('y', type=int)
        action_type = request.form.get('action_type', 'none')
        
        # Validazioni
        if not text:
            flash('Il testo della carta è obbligatorio', 'error')
            return redirect(request.url)
        
        if slot_col is None or slot_row is None:
            flash('Posizione non valida', 'error')
            return redirect(request.url)
        
        if slot_col < 0 or slot_col >= page.grid_cols or slot_row < 0 or slot_row >= page.grid_rows:
            flash(f'Posizione fuori dalla griglia ({page.grid_cols}×{page.grid_rows})', 'error')
            return redirect(request.url)
        
        # Verifica posizione libera (esclusa carta corrente)
        if slot_col != card.slot_col or slot_row != card.slot_row:
            existing_card = db.query(Card).filter_by(
                page_id=page_id, slot_col=slot_col, slot_row=slot_row
            ).filter(Card.id != card_id).first()
            
            if existing_card:
                flash(f'Posizione ({slot_col}, {slot_row}) già occupata', 'error')
                return redirect(request.url)
        
        # Gestione asset immagine
        image_asset_id = request.form.get('image_asset_id', type=int)
        if image_asset_id:
            asset = db.query(Asset).filter_by(id=image_asset_id).first()
            if not asset:
                flash('Asset selezionato non valido', 'error')
                return redirect(request.url)
        
        # Gestione azione navigazione
        target_page_id = None
        if action_type == 'navigation':
            target_page_id = request.form.get('target_page_id', type=int)
            if target_page_id:
                target_page = db.query(Page).filter_by(id=target_page_id, book_id=book_id).first()
                if not target_page:
                    flash('Pagina di destinazione non valida', 'error')
                    return redirect(request.url)
        
        # Aggiorna carta
        card.label = text
        card.slot_col = slot_col
        card.slot_row = slot_row
        card.target_page_id = target_page_id
        card.image_id = image_asset_id
        
        db.commit()
        
        flash(f'Carta "{text}" aggiornata con successo!', 'success')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
    
    except SQLAlchemyError as e:
        db.rollback()
        flash(f'Errore nell\'aggiornamento della carta: {str(e)}', 'error')
        return redirect(url_for('cards.view_card', book_id=book_id, page_id=page_id, card_id=card_id))
    finally:
        db.close()


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards/<int:card_id>/delete', methods=['POST'])
def delete_card(book_id, page_id, card_id):
    """Elimina una carta"""
    db = get_db()
    try:
        card = db.query(Card).filter_by(id=card_id, page_id=page_id).first()
        if not card:
            flash('Carta non trovata', 'error')
            return redirect(url_for('cards.list_cards', book_id=book_id, page_id=page_id))
        
        # Verifica appartenenza al libro
        if card.page.book.id != book_id:
            flash('Carta non appartiene al libro specificato', 'error')
            return redirect(url_for('books.list_books'))
        
        card_text = card.label
        db.delete(card)
        db.commit()
        
        flash(f'Carta "{card_text}" eliminata con successo!', 'success')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
    
    except SQLAlchemyError as e:
        db.rollback()
        flash(f'Errore nell\'eliminazione della carta: {str(e)}', 'error')
        return redirect(url_for('cards.view_card', book_id=book_id, page_id=page_id, card_id=card_id))
    finally:
        close_db(db)


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards/<int:card_id>/move', methods=['POST'])
def move_card(book_id, page_id, card_id):
    """Sposta una carta (AJAX)"""
    db = get_db()
    try:
        card = db.query(Card).filter_by(id=card_id, page_id=page_id).first()
        if not card:
            return jsonify({'success': False, 'message': 'Carta non trovata'}), 404
        
        # Verifica appartenenza al libro
        if card.page.book.id != book_id:
            return jsonify({'success': False, 'message': 'Carta non appartiene al libro'}), 403
        
        new_slot_col = request.json.get('x', type=int)
        new_slot_row = request.json.get('y', type=int)
        
        if new_slot_col is None or new_slot_row is None:
            return jsonify({'success': False, 'message': 'Posizione non valida'}), 400
        
        page = card.page
        if new_slot_col < 0 or new_slot_col >= page.grid_cols or new_slot_row < 0 or new_slot_row >= page.grid_rows:
            return jsonify({
                'success': False, 
                'message': f'Posizione fuori dalla griglia ({page.grid_cols}×{page.grid_rows})'
            }), 400
        
        # Verifica posizione libera
        existing_card = db.query(Card).filter_by(
            page_id=page_id, slot_col=new_slot_col, slot_row=new_slot_row
        ).filter(Card.id != card_id).first()
        
        if existing_card:
            return jsonify({
                'success': False, 
                'message': f'Posizione ({new_slot_col}, {new_slot_row}) già occupata'
            }), 409
        
        # Sposta carta
        old_position = (card.slot_col, card.slot_row)
        card.slot_col = new_slot_col
        card.slot_row = new_slot_row
        db.commit()

        return jsonify({
            'success': True,
            'message': f'Carta spostata da ({old_position[0]}, {old_position[1]}) a ({new_slot_col}, {new_slot_row})',
            'old_position': old_position,
            'new_position': (new_slot_col, new_slot_row)
        })
    
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({'success': False, 'message': f'Errore database: {str(e)}'}), 500
    finally:
        close_db(db)
def find_free_position(page, occupied_positions):
    """Trova la prima posizione libera nella griglia"""
    for y in range(page.grid_rows):
        for x in range(page.grid_cols):
            if (x, y) not in occupied_positions:
                return x, y
    # Se non trova posizioni libere, restituisce (0, 0)
    return 0, 0