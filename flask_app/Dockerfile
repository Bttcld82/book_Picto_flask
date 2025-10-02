# Flask AAC Builder - Dockerfile semplificato

FROM python:3.11-slim

# Variabili ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app

WORKDIR /app

# Installa dipendenze sistema (per Pillow)
RUN apt-get update && apt-get install -y \
    gcc libc6-dev \
    libjpeg-dev libpng-dev libfreetype6-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installa dipendenze Python
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copia applicazione
COPY . .

# Crea directory per media
RUN mkdir -p app/static/media && chmod 755 app/static/media

# Utente non-root
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Avvio
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:create_app()"]