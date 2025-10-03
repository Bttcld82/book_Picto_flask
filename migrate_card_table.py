#!/usr/bin/env python3
"""
Script di migrazione per aggiungere le nuove colonne al modello Card
"""

import sqlite3
import os

def migrate_database():
    db_path = os.path.join(os.path.dirname(__file__), 'data.db')
    
    if not os.path.exists(db_path):
        print("Database non trovato!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Controlla se le colonne esistono già
        cursor.execute("PRAGMA table_info(card)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'background_color' not in columns:
            migrations_needed.append("ALTER TABLE card ADD COLUMN background_color TEXT DEFAULT '#FFFFFF'")
            
        if 'border_color' not in columns:
            migrations_needed.append("ALTER TABLE card ADD COLUMN border_color TEXT DEFAULT '#000000'")
            
        if 'action_type' not in columns:
            migrations_needed.append("ALTER TABLE card ADD COLUMN action_type TEXT DEFAULT 'none'")
        
        if not migrations_needed:
            print("Tutte le colonne sono già presenti!")
            return
        
        print(f"Eseguendo {len(migrations_needed)} migrazioni...")
        
        for migration in migrations_needed:
            print(f"Eseguendo: {migration}")
            cursor.execute(migration)
        
        conn.commit()
        print("Migrazioni completate con successo!")
        
        # Verifica finale
        cursor.execute("PRAGMA table_info(card)")
        new_columns = [col[1] for col in cursor.fetchall()]
        print(f"Colonne nella tabella card: {new_columns}")
        
    except Exception as e:
        print(f"Errore durante la migrazione: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()