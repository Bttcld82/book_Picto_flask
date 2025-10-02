# 🔖 AAC Builder Flask App

Versione Flask Full-Stack dell'applicazione AAC Builder, convertita da FastAPI+Next.js.

## 🚀 Quick Start

### 1. Installazione Dipendenze
```bash
cd flask_app
pip install -e .
```

### 2. Avvio Development Server
```bash
python run.py
```

L'applicazione sarà disponibile su: **http://localhost:5000**

## 📁 Struttura

```
flask_app/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── routes/
│   │   ├── main.py          # Homepage e ricerca
│   │   └── books.py         # CRUD libri
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html        # Layout base
│   │   ├── index.html       # Homepage
│   │   ├── books/           # Template libri
│   │   └── components/      # Componenti riusabili
│   ├── static/
│   │   ├── css/main.css     # Stili principali
│   │   └── js/main.js       # JavaScript minimo
│   └── forms/               # WTForms (future)
├── pyproject.toml           # Dipendenze
├── run.py                   # Entry point
└── README.md               # Questa documentazione
```

## ✨ Funzionalità Implementate

### 🏠 Homepage
- Lista libri con ricerca
- Contatori e statistiche
- Design responsive
- Creazione rapida libro

### 📚 Gestione Libri
- **Lista libri** (`/books`)
- **Dettagli libro** (`/books/<id>`)
- **Crea libro** (`/books/new`)
- **Modifica libro** (`/books/<id>/edit`)
- **Elimina libro** (POST `/books/<id>/delete`)

### 🎨 UI/UX
- **Design dark theme** moderno
- **Responsive** per mobile/desktop
- **Flash messages** per feedback utente
- **Auto-save** bozze form
- **Keyboard shortcuts** (Ctrl+N, Ctrl+/, ESC)
- **Loading states** su form submission

## 🔧 Features Tecniche

### Backend
- ✅ **Flask** con Blueprint pattern
- ✅ **SQLAlchemy** (riutilizza modelli esistenti)
- ✅ **Jinja2** templates con macro
- ✅ **CORS** support per development
- ✅ **Error handling** e flash messages

### Frontend
- ✅ **Server-side rendering** completo
- ✅ **CSS custom** (no framework esterni)
- ✅ **JavaScript minimo** per UX essenziali
- ✅ **Auto-save** e localStorage
- ✅ **Live preview** in form edit

### Database
- ✅ **Riutilizzo modelli** dal backend FastAPI esistente
- ✅ **Stesso database** SQLite
- ✅ **Transazioni sicure** con rollback

## 🔄 Confronto con Versione Originale

| Aspetto | FastAPI+Next.js | Flask Full-Stack |
|---------|-----------------|------------------|
| **Architettura** | Separata (2 server) | Unificata (1 server) |
| **Dipendenze** | ~50 npm + ~10 pip | ~15 pip |
| **Build time** | ~30s (Next.js) | ~2s (no build) |
| **Deploy** | 2 container | 1 container |
| **Debug** | 2 stack trace | 1 stack trace |
| **SEO** | CSR + SSG | SSR nativo |
| **Linguaggi** | Python + TypeScript | Python only |

## 🚧 Funzionalità in Sviluppo

- [ ] **Gestione Pagine** (`/books/<id>/pages`)
- [ ] **Gestione Carte** (`/pages/<id>/cards`)
- [ ] **Upload Immagini** (`/assets`)
- [ ] **Export/Import** libri
- [ ] **Sistema Runtime** per visualizzazione

## 🎯 Prossimi Passi

1. **Testing parallelo** con versione FastAPI
2. **Implementazione pagine** e carte
3. **Sistema upload** file e media
4. **Migrazione completa** dati
5. **Rimozione** stack precedente

## 🔧 Development

### Hot Reload
Il server Flask ricarica automaticamente i file quando modificati:
- ✅ **Python files** → Restart automatico
- ✅ **Templates** → Reload immediato
- ✅ **Static files** → Refresh browser

### Debug
```bash
# Con debug dettagliato
FLASK_DEBUG=1 python run.py

# Con profiling
FLASK_ENV=development python run.py
```

### Database
```bash
# Reset database (se necessario)
rm ../backend/data.db
python run.py  # Ricrea automaticamente
```

## 📊 Performance

### Metriche Attese
- **First Paint**: < 500ms
- **Page Load**: < 1s
- **Memory Usage**: ~50MB (vs ~200MB Next.js)
- **Bundle Size**: 0 (server-side)

### Ottimizzazioni
- ✅ **Minimal JavaScript** (~2KB)
- ✅ **CSS ottimizzato** (~15KB)
- ✅ **Compressione gzip** automatica
- ✅ **Static file caching**

## 🚀 Production Deployment

```dockerfile
# Dockerfile esempio
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

```bash
# Docker build & run
docker build -t aac-flask .
docker run -p 5000:5000 aac-flask
```

## 📝 Note di Migrazione

### Compatibilità Database
- ✅ **Stessi modelli** SQLAlchemy
- ✅ **Stesso schema** database
- ✅ **Nessuna migrazione** dati necessaria

### URL Mapping
- `http://localhost:3000/` → `http://localhost:5000/`
- `http://localhost:8000/api/books` → `http://localhost:5000/books`
- API REST → Server-side forms

### Data Flow
```
Prima:  Browser → Next.js → fetch() → FastAPI → Database
Dopo:   Browser → Flask → SQLAlchemy → Database
```

## 🔍 Troubleshooting

### Errore "Module not found"
```bash
# Assicurati di essere nella cartella corretta
cd flask_app
pip install -e .
```

### Porta già in uso
```bash
# Cambia porta in run.py o killa processo
lsof -ti:5000 | xargs kill -9  # Linux/Mac
netstat -ano | findstr :5000   # Windows
```

### Database lock
```bash
# Chiudi tutte le connessioni e riavvia
rm ../backend/data.db
python run.py
```

---

**Status**: ✅ **MVP Completato**  
**Version**: 1.0.0  
**Last Update**: Ottobre 2025