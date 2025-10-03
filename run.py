#!/usr/bin/env python3
"""
AAC Builder Flask App
Applicazione Flask completa e autonoma

Run: python run.py
"""

from app import create_app

# Crea l'applicazione Flask
app = create_app()

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )