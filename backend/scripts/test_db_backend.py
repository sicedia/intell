"""
Test script to verify that the retry-enabled database backend is being used.

Run this script to check if the custom backend is configured:
    python scripts/test_db_backend.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings
from django.db import connections

def main():
    print("Checking database backend configuration...")
    print()
    
    # Check default database
    db_config = settings.DATABASES.get('default', {})
    engine = db_config.get('ENGINE', 'Unknown')
    
    print(f"Database ENGINE: {engine}")
    
    if 'apps.core.db.backends.postgresql' in engine:
        print("✓ Using retry-enabled PostgreSQL backend")
    elif 'postgresql' in engine:
        print("⚠ Using standard PostgreSQL backend (retry not enabled)")
        print("  Consider using 'apps.core.db.backends.postgresql' for retry support")
    else:
        print(f"ℹ Using {engine} backend")
    
    print()
    print("Testing connection...")
    
    try:
        conn = connections['default']
        conn.ensure_connection()
        print("✓ Database connection successful")
        
        # Check if it's using our custom backend
        backend_class = type(conn).__name__
        print(f"Backend class: {backend_class}")
        
        if 'PostgreSQLDatabaseWrapper' in backend_class:
            print("✓ Confirmed: Using retry-enabled backend")
        else:
            print("⚠ Using standard backend")
            
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print()
        print("This is expected if the database is not running.")
        print("With retry-enabled backend, you should see retry messages above.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
