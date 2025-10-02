"""
Route per la gestione delle Carte AAC
Gestisce il CRUD completo delle carte con grid editor
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from sqlalchemy.exc import SQLAlchemyError
from app.db import get_db_session
from app.models.book import Book
from app.models.page import Page
from app.models.card import Card
from app.models.asset import Asset

cards_bp = Blueprint('cards', __name__)


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards')
def list_cards(book_id, page_id):
    """Lista tutte le carte di una pagina specifica"""
    session = get_db_session()
    try:
        # Verifica esistenza book e page
        book = session.query(Book).filter_by(id=book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        page = session.query(Page).filter_by(id=page_id, book_id=book_id).first()
        if not page:
            flash('Pagina non trovata', 'error')
            return redirect(url_for('pages.list_pages', book_id=book_id))
        
        # Recupera tutte le carte della pagina ordinate per posizione
        cards = session.query(Card).filter_by(page_id=page_id).order_by(Card.y, Card.x).all()
        
        return render_template('cards/list.html', 
                             book=book, 
                             page=page, 
                             cards=cards)
    
    except SQLAlchemyError as e:
        flash(f'Errore database: {str(e)}', 'error')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
    finally:
        session.close()


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards/<int:card_id>')
def view_card(book_id, page_id, card_id):
    """Visualizza una carta specifica"""
    session = get_db_session()
    try:
        # Verifica esistenza e relazioni
        card = session.query(Card).filter_by(
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
        session.close()


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards/new', methods=['GET', 'POST'])
def create_card(book_id, page_id):
    """Crea una nuova carta"""
    session = get_db_session()
    try:
        # Verifica esistenza book e page
        book = session.query(Book).filter_by(id=book_id).first()
        if not book:
            flash('Libro non trovato', 'error')
            return redirect(url_for('books.list_books'))
        
        page = session.query(Page).filter_by(id=page_id, book_id=book_id).first()
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
                occupied_positions = {(card.x, card.y) for card in page.cards}
                suggested_x, suggested_y = find_free_position(page, occupied_positions)
            
            # Lista asset disponibili per selezione
            assets = session.query(Asset).order_by(Asset.created_at.desc()).all()
            
            return render_template('cards/new.html',
                                 book=book,
                                 page=page,
                                 suggested_x=suggested_x,
                                 suggested_y=suggested_y,
                                 assets=assets)
        
        # POST: crea la carta
        text = request.form.get('text', '').strip()
        x = request.form.get('x', type=int)
        y = request.form.get('y', type=int)
        background_color = request.form.get('background_color', '#FFFFFF')
        border_color = request.form.get('border_color', '#000000')
        action_type = request.form.get('action_type', 'none')
        
        # Validazioni
        if not text:
            flash('Il testo della carta è obbligatorio', 'error')
            return redirect(request.url)
        
        if x is None or y is None:
            flash('Posizione non valida', 'error')
            return redirect(request.url)
        
        if x < 0 or x >= page.grid_cols or y < 0 or y >= page.grid_rows:
            flash(f'Posizione fuori dalla griglia ({page.grid_cols}×{page.grid_rows})', 'error')
            return redirect(request.url)
        
        # Verifica posizione libera
        existing_card = session.query(Card).filter_by(page_id=page_id, x=x, y=y).first()
        if existing_card:
            flash(f'Posizione ({x}, {y}) già occupata', 'error')
            return redirect(request.url)
        
        # Gestione asset immagine
        image_asset_id = request.form.get('image_asset_id', type=int)
        if image_asset_id:
            asset = session.query(Asset).filter_by(id=image_asset_id).first()
            if not asset:
                flash('Asset selezionato non valido', 'error')
                return redirect(request.url)
        
        # Gestione azione navigazione
        target_page_id = None
        if action_type == 'navigation':
            target_page_id = request.form.get('target_page_id', type=int)
            if target_page_id:
                target_page = session.query(Page).filter_by(id=target_page_id, book_id=book_id).first()
                if not target_page:
                    flash('Pagina di destinazione non valida', 'error')
                    return redirect(request.url)
        
        # Crea nuova carta
        new_card = Card(
            text=text,
            x=x,
            y=y,
            background_color=background_color,
            border_color=border_color,
            action_type=action_type,
            target_page_id=target_page_id,
            image_asset_id=image_asset_id,
            page_id=page_id
        )
        
        session.add(new_card)
        session.commit()
        
        flash(f'Carta "{text}" creata con successo!', 'success')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
    
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Errore nella creazione della carta: {str(e)}', 'error')
        return redirect(url_for('cards.list_cards', book_id=book_id, page_id=page_id))
    finally:
        session.close()


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards/<int:card_id>/edit', methods=['GET', 'POST'])
def edit_card(book_id, page_id, card_id):
    """Modifica una carta esistente"""
    session = get_db_session()
    try:
        # Verifica esistenza carta
        card = session.query(Card).filter_by(id=card_id, page_id=page_id).first()
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
            assets = session.query(Asset).order_by(Asset.created_at.desc()).all()
            pages = session.query(Page).filter_by(book_id=book_id).order_by(Page.order).all()
            
            return render_template('cards/edit.html',
                                 book=book,
                                 page=page,
                                 card=card,
                                 assets=assets,
                                 pages=pages)
        
        # POST: aggiorna la carta
        text = request.form.get('text', '').strip()
        x = request.form.get('x', type=int)
        y = request.form.get('y', type=int)
        background_color = request.form.get('background_color', '#FFFFFF')
        border_color = request.form.get('border_color', '#000000')
        action_type = request.form.get('action_type', 'none')
        
        # Validazioni
        if not text:
            flash('Il testo della carta è obbligatorio', 'error')
            return redirect(request.url)
        
        if x is None or y is None:
            flash('Posizione non valida', 'error')
            return redirect(request.url)
        
        if x < 0 or x >= page.grid_cols or y < 0 or y >= page.grid_rows:
            flash(f'Posizione fuori dalla griglia ({page.grid_cols}×{page.grid_rows})', 'error')
            return redirect(request.url)
        
        # Verifica posizione libera (esclusa carta corrente)
        if x != card.x or y != card.y:
            existing_card = session.query(Card).filter_by(
                page_id=page_id, x=x, y=y
            ).filter(Card.id != card_id).first()
            
            if existing_card:
                flash(f'Posizione ({x}, {y}) già occupata', 'error')
                return redirect(request.url)
        
        # Gestione asset immagine
        image_asset_id = request.form.get('image_asset_id', type=int)
        if image_asset_id:
            asset = session.query(Asset).filter_by(id=image_asset_id).first()
            if not asset:
                flash('Asset selezionato non valido', 'error')
                return redirect(request.url)
        
        # Gestione azione navigazione
        target_page_id = None
        if action_type == 'navigation':
            target_page_id = request.form.get('target_page_id', type=int)
            if target_page_id:
                target_page = session.query(Page).filter_by(id=target_page_id, book_id=book_id).first()
                if not target_page:
                    flash('Pagina di destinazione non valida', 'error')
                    return redirect(request.url)
        
        # Aggiorna carta
        card.text = text
        card.x = x
        card.y = y
        card.background_color = background_color
        card.border_color = border_color
        card.action_type = action_type
        card.target_page_id = target_page_id
        card.image_asset_id = image_asset_id
        
        session.commit()
        
        flash(f'Carta "{text}" aggiornata con successo!', 'success')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
    
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Errore nell\'aggiornamento della carta: {str(e)}', 'error')
        return redirect(url_for('cards.view_card', book_id=book_id, page_id=page_id, card_id=card_id))
    finally:
        session.close()


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards/<int:card_id>/delete', methods=['POST'])
def delete_card(book_id, page_id, card_id):
    """Elimina una carta"""
    session = get_db_session()
    try:
        card = session.query(Card).filter_by(id=card_id, page_id=page_id).first()
        if not card:
            flash('Carta non trovata', 'error')
            return redirect(url_for('cards.list_cards', book_id=book_id, page_id=page_id))
        
        # Verifica appartenenza al libro
        if card.page.book.id != book_id:
            flash('Carta non appartiene al libro specificato', 'error')
            return redirect(url_for('books.list_books'))
        
        card_text = card.text
        session.delete(card)
        session.commit()
        
        flash(f'Carta "{card_text}" eliminata con successo!', 'success')
        return redirect(url_for('pages.view_page', book_id=book_id, page_id=page_id))
    
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Errore nell\'eliminazione della carta: {str(e)}', 'error')
        return redirect(url_for('cards.view_card', book_id=book_id, page_id=page_id, card_id=card_id))
    finally:
        session.close()


@cards_bp.route('/books/<int:book_id>/pages/<int:page_id>/cards/<int:card_id>/move', methods=['POST'])
def move_card(book_id, page_id, card_id):
    """Sposta una carta (AJAX)"""
    session = get_db_session()
    try:
        card = session.query(Card).filter_by(id=card_id, page_id=page_id).first()
        if not card:
            return jsonify({'success': False, 'message': 'Carta non trovata'}), 404
        
        # Verifica appartenenza al libro
        if card.page.book.id != book_id:
            return jsonify({'success': False, 'message': 'Carta non appartiene al libro'}), 403
        
        new_x = request.json.get('x', type=int)
        new_y = request.json.get('y', type=int)
        
        if new_x is None or new_y is None:
            return jsonify({'success': False, 'message': 'Posizione non valida'}), 400
        
        page = card.page
        if new_x < 0 or new_x >= page.grid_cols or new_y < 0 or new_y >= page.grid_rows:
            return jsonify({
                'success': False, 
                'message': f'Posizione fuori dalla griglia ({page.grid_cols}×{page.grid_rows})'
            }), 400
        
        # Verifica posizione libera
        existing_card = session.query(Card).filter_by(
            page_id=page_id, x=new_x, y=new_y
        ).filter(Card.id != card_id).first()
        
        if existing_card:
            return jsonify({
                'success': False, 
                'message': f'Posizione ({new_x}, {new_y}) già occupata'
            }), 409
        
        # Sposta carta
        old_position = (card.x, card.y)
        card.x = new_x
        card.y = new_y
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Carta spostata da ({old_position[0]}, {old_position[1]}) a ({new_x}, {new_y})',
            'old_position': old_position,
            'new_position': (new_x, new_y)
        })
    
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'success': False, 'message': f'Errore database: {str(e)}'}), 500
    finally:
        session.close()


def find_free_position(page, occupied_positions):
    """Trova la prima posizione libera nella griglia"""
    for y in range(page.grid_rows):
        for x in range(page.grid_cols):
            if (x, y) not in occupied_positions:
                return x, y
    # Se non trova posizioni libere, restituisce (0, 0)
    return 0, 0