"""
Route per la gestione degli Asset (immagini/media)
Gestisce upload, visualizzazione, modifica e eliminazione di asset
"""

import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory
from sqlalchemy.exc import SQLAlchemyError
from PIL import Image
import mimetypes
from app.db import get_db_session
from app.models.asset import Asset
from app.models.card import Card

assets_bp = Blueprint('assets', __name__)

# Configurazioni per upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
IMAGE_SIZES = {
    'thumbnail': (150, 150),
    'medium': (400, 400),
    'large': (800, 800)
}

def allowed_file(filename):
    """Controlla se il file ha un'estensione permessa"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_info(file):
    """Ottiene informazioni su un file caricato"""
    if not file or not file.filename:
        return None
    
    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return None
    
    # Genera nome unico per il file
    file_ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    
    return {
        'original_filename': filename,
        'filename': unique_filename,
        'extension': file_ext,
        'mimetype': file.mimetype or mimetypes.guess_type(filename)[0]
    }

def process_image(file_path, sizes=None):
    """Processa un'immagine creando diverse dimensioni"""
    if not sizes:
        sizes = IMAGE_SIZES
    
    try:
        with Image.open(file_path) as img:
            # Converti in RGB se necessario
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Ottieni dimensioni originali
            original_size = img.size
            
            # Crea versioni ridimensionate
            processed_sizes = {'original': original_size}
            
            base_path = os.path.splitext(file_path)[0]
            
            for size_name, (width, height) in sizes.items():
                # Ridimensiona mantenendo proporzioni
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                
                # Salva versione ridimensionata
                size_path = f"{base_path}_{size_name}.jpg"
                img.save(size_path, 'JPEG', quality=90, optimize=True)
                
                processed_sizes[size_name] = img.size
                
                # Ripristina immagine originale per prossimo ridimensionamento
                img = Image.open(file_path)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
            
            return processed_sizes
            
    except Exception as e:
        print(f"Errore nel processamento dell'immagine: {e}")
        return None


@assets_bp.route('/assets')
def list_assets():
    """Lista tutti gli asset disponibili"""
    session = get_db_session()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        file_type = request.args.get('type', '', type=str)
        
        # Query base
        query = session.query(Asset)
        
        # Filtro per ricerca
        if search:
            query = query.filter(Asset.filename.ilike(f'%{search}%'))
        
        # Filtro per tipo file
        if file_type:
            query = query.filter(Asset.mimetype.like(f'{file_type}%'))
        
        # Ordinamento
        sort_by = request.args.get('sort', 'created_at')
        sort_order = request.args.get('order', 'desc')
        
        if sort_by == 'filename':
            order_column = Asset.filename
        elif sort_by == 'size':
            order_column = Asset.file_size
        else:  # created_at
            order_column = Asset.created_at
        
        if sort_order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # Paginazione
        assets = query.offset((page - 1) * per_page).limit(per_page).all()
        total_assets = query.count()
        
        # Statistiche
        stats = {
            'total': session.query(Asset).count(),
            'images': session.query(Asset).filter(Asset.mimetype.like('image%')).count(),
            'total_size': session.query(Asset).with_entities(
                session.query(Asset.file_size).label('total_size')
            ).scalar() or 0
        }
        
        return render_template('assets/list.html',
                             assets=assets,
                             total_assets=total_assets,
                             page=page,
                             per_page=per_page,
                             search=search,
                             file_type=file_type,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             stats=stats)
    
    except SQLAlchemyError as e:
        flash(f'Errore database: {str(e)}', 'error')
        return redirect(url_for('main.index'))
    finally:
        session.close()


@assets_bp.route('/assets/upload', methods=['GET', 'POST'])
def upload_asset():
    """Upload di un nuovo asset"""
    if request.method == 'GET':
        return render_template('assets/upload.html')
    
    session = get_db_session()
    try:
        files = request.files.getlist('files')
        
        if not files or all(not file.filename for file in files):
            flash('Nessun file selezionato', 'error')
            return redirect(request.url)
        
        uploaded_assets = []
        errors = []
        
        # Crea directory se non esiste
        upload_dir = os.path.join(current_app.static_folder, 'media')
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in files:
            if not file.filename:
                continue
            
            # Controlli di validazione
            if file.content_length and file.content_length > MAX_FILE_SIZE:
                errors.append(f'{file.filename}: File troppo grande (max 10MB)')
                continue
            
            file_info = get_file_info(file)
            if not file_info:
                errors.append(f'{file.filename}: Tipo di file non supportato')
                continue
            
            # Controlla se il file esiste già
            existing_asset = session.query(Asset).filter_by(
                filename=file_info['original_filename']
            ).first()
            
            if existing_asset:
                errors.append(f'{file.filename}: File già esistente')
                continue
            
            # Salva file
            file_path = os.path.join(upload_dir, file_info['filename'])
            file.save(file_path)
            
            # Ottieni dimensioni e processa immagini
            file_size = os.path.getsize(file_path)
            width, height = None, None
            
            if file_info['mimetype'] and file_info['mimetype'].startswith('image/'):
                try:
                    # Processa immagine e crea thumbnail
                    sizes = process_image(file_path)
                    if sizes:
                        width, height = sizes['original']
                except Exception as e:
                    print(f"Errore nel processamento dell'immagine {file.filename}: {e}")
            
            # Crea record nel database
            new_asset = Asset(
                filename=file_info['filename'],
                original_filename=file_info['original_filename'],
                mimetype=file_info['mimetype'],
                file_size=file_size,
                width=width,
                height=height
            )
            
            session.add(new_asset)
            uploaded_assets.append(new_asset)
        
        if uploaded_assets:
            session.commit()
            flash(f'{len(uploaded_assets)} file caricati con successo!', 'success')
        
        if errors:
            for error in errors:
                flash(error, 'warning')
        
        if not uploaded_assets and not errors:
            flash('Nessun file da caricare', 'info')
        
        return redirect(url_for('assets.list_assets'))
    
    except Exception as e:
        session.rollback()
        flash(f'Errore durante l\'upload: {str(e)}', 'error')
        return redirect(request.url)
    finally:
        session.close()


@assets_bp.route('/assets/<int:asset_id>')
def view_asset(asset_id):
    """Visualizza un asset specifico"""
    session = get_db_session()
    try:
        asset = session.query(Asset).filter_by(id=asset_id).first()
        if not asset:
            flash('Asset non trovato', 'error')
            return redirect(url_for('assets.list_assets'))
        
        # Trova carte che usano questo asset
        cards_using_asset = session.query(Card).filter_by(image_asset_id=asset_id).all()
        
        return render_template('assets/detail.html',
                             asset=asset,
                             cards_using_asset=cards_using_asset)
    
    except SQLAlchemyError as e:
        flash(f'Errore database: {str(e)}', 'error')
        return redirect(url_for('assets.list_assets'))
    finally:
        session.close()


@assets_bp.route('/assets/<int:asset_id>/edit', methods=['GET', 'POST'])
def edit_asset(asset_id):
    """Modifica un asset"""
    session = get_db_session()
    try:
        asset = session.query(Asset).filter_by(id=asset_id).first()
        if not asset:
            flash('Asset non trovato', 'error')
            return redirect(url_for('assets.list_assets'))
        
        if request.method == 'GET':
            return render_template('assets/edit.html', asset=asset)
        
        # POST: aggiorna asset
        new_filename = request.form.get('filename', '').strip()
        
        if not new_filename:
            flash('Il nome del file è obbligatorio', 'error')
            return redirect(request.url)
        
        # Controlla se il nuovo nome è già in uso
        if new_filename != asset.original_filename:
            existing = session.query(Asset).filter_by(
                original_filename=new_filename
            ).filter(Asset.id != asset_id).first()
            
            if existing:
                flash('Nome file già in uso', 'error')
                return redirect(request.url)
        
        asset.original_filename = new_filename
        session.commit()
        
        flash('Asset aggiornato con successo!', 'success')
        return redirect(url_for('assets.view_asset', asset_id=asset_id))
    
    except SQLAlchemyError as e:
        session.rollback()
        flash(f'Errore nell\'aggiornamento: {str(e)}', 'error')
        return redirect(url_for('assets.view_asset', asset_id=asset_id))
    finally:
        session.close()


@assets_bp.route('/assets/<int:asset_id>/delete', methods=['POST'])
def delete_asset(asset_id):
    """Elimina un asset"""
    session = get_db_session()
    try:
        asset = session.query(Asset).filter_by(id=asset_id).first()
        if not asset:
            flash('Asset non trovato', 'error')
            return redirect(url_for('assets.list_assets'))
        
        # Controlla se è usato da qualche carta
        cards_using = session.query(Card).filter_by(image_asset_id=asset_id).count()
        
        if cards_using > 0:
            flash(f'Impossibile eliminare: asset usato da {cards_using} carte', 'error')
            return redirect(url_for('assets.view_asset', asset_id=asset_id))
        
        # Elimina file fisico
        file_path = os.path.join(current_app.static_folder, 'media', asset.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
            # Elimina anche versioni ridimensionate
            base_path = os.path.splitext(file_path)[0]
            for size_name in IMAGE_SIZES.keys():
                size_path = f"{base_path}_{size_name}.jpg"
                if os.path.exists(size_path):
                    os.remove(size_path)
        
        # Elimina record dal database
        asset_filename = asset.original_filename
        session.delete(asset)
        session.commit()
        
        flash(f'Asset "{asset_filename}" eliminato con successo!', 'success')
        return redirect(url_for('assets.list_assets'))
    
    except Exception as e:
        session.rollback()
        flash(f'Errore nell\'eliminazione: {str(e)}', 'error')
        return redirect(url_for('assets.view_asset', asset_id=asset_id))
    finally:
        session.close()


@assets_bp.route('/assets/api/upload', methods=['POST'])
def api_upload():
    """API endpoint per upload AJAX"""
    session = get_db_session()
    try:
        file = request.files.get('file')
        
        if not file or not file.filename:
            return jsonify({'success': False, 'message': 'Nessun file selezionato'}), 400
        
        # Validazioni
        if file.content_length and file.content_length > MAX_FILE_SIZE:
            return jsonify({'success': False, 'message': 'File troppo grande (max 10MB)'}), 400
        
        file_info = get_file_info(file)
        if not file_info:
            return jsonify({'success': False, 'message': 'Tipo di file non supportato'}), 400
        
        # Controlla duplicati
        existing = session.query(Asset).filter_by(
            filename=file_info['original_filename']
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'File già esistente'}), 409
        
        # Salva file
        upload_dir = os.path.join(current_app.static_folder, 'media')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file_info['filename'])
        file.save(file_path)
        
        # Processa immagine
        file_size = os.path.getsize(file_path)
        width, height = None, None
        
        if file_info['mimetype'] and file_info['mimetype'].startswith('image/'):
            try:
                sizes = process_image(file_path)
                if sizes:
                    width, height = sizes['original']
            except Exception as e:
                print(f"Errore processamento immagine: {e}")
        
        # Crea record
        new_asset = Asset(
            filename=file_info['filename'],
            original_filename=file_info['original_filename'],
            mimetype=file_info['mimetype'],
            file_size=file_size,
            width=width,
            height=height
        )
        
        session.add(new_asset)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'File caricato con successo',
            'asset': {
                'id': new_asset.id,
                'filename': new_asset.filename,
                'original_filename': new_asset.original_filename,
                'url': url_for('static', filename=f'media/{new_asset.filename}'),
                'mimetype': new_asset.mimetype,
                'file_size': new_asset.file_size,
                'width': new_asset.width,
                'height': new_asset.height
            }
        })
    
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': f'Errore: {str(e)}'}), 500
    finally:
        session.close()


@assets_bp.route('/assets/<path:filename>')
def serve_asset(filename):
    """Serve file statici degli asset"""
    return send_from_directory(
        os.path.join(current_app.static_folder, 'media'),
        filename
    )