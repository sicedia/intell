#!/usr/bin/env python
"""
Development setup script for Intelli backend.

This script automates the initial setup process:
1. Checks if infrastructure services are running
2. Verifies database connectivity
3. Runs Django migrations
4. Creates a superuser (optional)

Usage:
    python scripts/setup_dev.py [--skip-superuser]
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.core.management import call_command
from django.db import connection
from decouple import config


def print_step(message):
    """Print a formatted step message."""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}\n")


def check_docker_compose():
    """Check if docker-compose is available."""
    try:
        subprocess.run(
            ['docker-compose', '--version'],
            check=True,
            capture_output=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_infrastructure_running():
    """Check if infrastructure services are running."""
    print_step("Checking infrastructure services...")
    
    if not check_docker_compose():
        print("❌ docker-compose not found. Please install Docker Compose.")
        return False
    
    # Check if services are running
    try:
        result = subprocess.run(
            ['docker-compose', '-f', 'infrastructure/docker-compose.yml', 'ps'],
            capture_output=True,
            text=True,
            cwd=BACKEND_DIR.parent
        )
        
        if 'db' not in result.stdout or 'redis' not in result.stdout:
            print("❌ Infrastructure services are not running.")
            print("   Please start them with: cd infrastructure && docker-compose up -d")
            return False
        
        print("✅ Infrastructure services are running.")
        return True
    except Exception as e:
        print(f"❌ Error checking infrastructure: {e}")
        return False


def wait_for_database(max_retries=30, delay=2):
    """Wait for database to be ready."""
    print_step("Waiting for database to be ready...")
    
    for i in range(max_retries):
        try:
            connection.ensure_connection()
            print("✅ Database is ready!")
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"   Attempt {i+1}/{max_retries}: Database not ready yet, waiting...")
                time.sleep(delay)
            else:
                print(f"❌ Database connection failed after {max_retries} attempts: {e}")
                return False
    
    return False


def run_migrations():
    """Run Django migrations."""
    print_step("Running database migrations...")
    
    try:
        call_command('makemigrations', verbosity=1)
        call_command('migrate', verbosity=1)
        print("✅ Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def create_superuser():
    """Create a superuser interactively."""
    print_step("Creating superuser...")
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            print("✅ Superuser already exists. Skipping creation.")
            return True
        
        print("Creating a new superuser account...")
        call_command('createsuperuser', interactive=True)
        print("✅ Superuser created successfully!")
        return True
    except KeyboardInterrupt:
        print("\n⚠️  Superuser creation cancelled.")
        return True
    except Exception as e:
        print(f"❌ Failed to create superuser: {e}")
        return False


def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup development environment')
    parser.add_argument(
        '--skip-superuser',
        action='store_true',
        help='Skip superuser creation'
    )
    parser.add_argument(
        '--skip-infrastructure-check',
        action='store_true',
        help='Skip infrastructure service check'
    )
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  Intelli Backend - Development Setup")
    print("="*60 + "\n")
    
    # Check infrastructure
    if not args.skip_infrastructure_check:
        if not check_infrastructure_running():
            print("\n⚠️  Please start infrastructure services first:")
            print("   cd infrastructure && docker-compose up -d")
            sys.exit(1)
    
    # Wait for database
    if not wait_for_database():
        print("\n⚠️  Database is not ready. Please check your infrastructure services.")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        print("\n❌ Setup failed during migrations.")
        sys.exit(1)
    
    # Create superuser
    if not args.skip_superuser:
        create_superuser()
    
    print("\n" + "="*60)
    print("  ✅ Setup completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Start Django server: python manage.py runserver")
    print("  2. Start Celery workers (see backend/README.md)")
    print("  3. Access admin at: http://localhost:8000/admin/")
    print()


if __name__ == '__main__':
    main()

