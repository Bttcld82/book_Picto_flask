"""
Schemas module for Flask app
Obiettivo: usare (se disponibili) gli schema Pydantic del backend FastAPI,
senza confliggere con il package locale "app" di questa Flask app.

Se il backend non è presente, esporta fallback a None in modo silenzioso.
"""

from __future__ import annotations

import os
import importlib.util
from types import ModuleType
from typing import Any, Tuple

# Percorso del backend (se esiste affiancato a questa repo)
BACKEND_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend')
)

def _load_backend_module(module_rel_path: str, module_name: str) -> ModuleType | None:
    """Carica un modulo del backend da file path, evitando l'uso di sys.path
    che potrebbe collidere con il package locale 'app'.
    module_rel_path es: 'app/schemas/book.py'
    module_name es: 'backend_schemas_book'
    """
    full_path = os.path.join(BACKEND_PATH, module_rel_path)
    if not os.path.isfile(full_path):
        return None
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return mod
        except Exception:
            return None
    return None

def _import_classes(mod: ModuleType | None, names: Tuple[str, ...]) -> Tuple[Any, ...]:
    if mod is None:
        return tuple([None for _ in names])
    out = []
    for name in names:
        out.append(getattr(mod, name, None))
    return tuple(out)

# Prova a caricare gli schema dal backend, se presenti
BookCreate = BookUpdate = BookRead = None
PageCreate = PageUpdate = PageRead = None
CardCreate = CardUpdate = CardRead = None
AssetCreate = AssetUpdate = AssetRead = None

if os.path.isdir(BACKEND_PATH):
    book_mod = _load_backend_module(os.path.join('app', 'schemas', 'book.py'), 'backend_schemas_book')
    page_mod = _load_backend_module(os.path.join('app', 'schemas', 'page.py'), 'backend_schemas_page')
    card_mod = _load_backend_module(os.path.join('app', 'schemas', 'card.py'), 'backend_schemas_card')
    asset_mod = _load_backend_module(os.path.join('app', 'schemas', 'asset.py'), 'backend_schemas_asset')

    (BookCreate, BookUpdate, BookRead) = _import_classes(book_mod, ("BookCreate", "BookUpdate", "BookRead"))
    (PageCreate, PageUpdate, PageRead) = _import_classes(page_mod, ("PageCreate", "PageUpdate", "PageRead"))
    (CardCreate, CardUpdate, CardRead) = _import_classes(card_mod, ("CardCreate", "CardUpdate", "CardRead"))
    (AssetCreate, AssetUpdate, AssetRead) = _import_classes(asset_mod, ("AssetCreate", "AssetUpdate", "AssetRead"))

# Re-export per uso nel Flask app (principalmente per validazione)
__all__ = [
    'BookCreate', 'BookUpdate', 'BookRead',
    'PageCreate', 'PageUpdate', 'PageRead',
    'CardCreate', 'CardUpdate', 'CardRead',
    'AssetCreate', 'AssetUpdate', 'AssetRead'
]