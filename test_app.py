#!/usr/bin/env python3
"""
Test rapido per verificare che la Flask app funzioni correttamente
"""

import os
import sys

# Aggiungi il path corrente
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

def test_imports():
    """Test degli import principali"""
    print("🧪 Testing imports...")
    
    try:
        # Test import Flask app
        from app import create_app
        print("✅ Flask app import OK")
        
        # Test import database
        from app.db import get_db, close_db, init_db
        print("✅ Database imports OK")
        
        # Test import modelli
        from app.models import Book
        print("✅ Models import OK")
        
        # Test import routes
        from app.routes.main import main_bp
        from app.routes.books import books_bp
        print("✅ Routes import OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test creazione app Flask"""
    print("\n🧪 Testing app creation...")
    
    try:
        from app import create_app
        app = create_app()
        
        print(f"✅ App created: {app}")
        print(f"✅ Secret key configured: {bool(app.config.get('SECRET_KEY'))}")
        print(f"✅ Upload folder: {app.config.get('UPLOAD_FOLDER')}")
        
        # Test che i blueprint siano registrati
        blueprints = [bp.name for bp in app.blueprints.values()]
        print(f"✅ Blueprints registered: {blueprints}")
        
        return True
        
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

def test_database_connection():
    """Test connessione database"""
    print("\n🧪 Testing database connection...")
    
    try:
        from app.db import get_db, close_db
        from app.models import Book
        
        # Test connessione
        db = get_db()
        print("✅ Database connection OK")
        
        # Test query semplice (conta libri)
        count = db.query(Book).count()
        print(f"✅ Books in database: {count}")
        
        close_db(db)
        print("✅ Database connection closed OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Flask App Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_app_creation, 
        test_database_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready to run Flask app")
        print("\n🚀 To start the app run:")
        print("   python run.py")
        print("\n🌐 Then visit: http://localhost:5000")
    else:
        print("❌ Some tests failed. Check errors above.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)