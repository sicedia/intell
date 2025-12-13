#!/usr/bin/env python
"""
Script to check infrastructure connectivity (PostgreSQL, Redis).
Run this to verify docker-compose services are accessible.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.conf import settings
from django.db import connection
import redis
from channels.layers import get_channel_layer


def check_postgresql():
    """Check PostgreSQL connection."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✅ PostgreSQL: Connected")
                return True
    except Exception as e:
        print(f"❌ PostgreSQL: Connection failed - {e}")
        return False


def check_redis_celery():
    """Check Redis connection for Celery."""
    try:
        broker_url = settings.CELERY_BROKER_URL
        r = redis.from_url(broker_url)
        r.ping()
        print(f"✅ Redis (Celery): Connected to {broker_url}")
        return True
    except Exception as e:
        print(f"❌ Redis (Celery): Connection failed - {e}")
        return False


def check_redis_channels():
    """Check Redis connection for Channels."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            # Simple connection test - just verify it's configured
            redis_url = settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
            r = redis.from_url(redis_url)
            r.ping()
            print(f"✅ Redis (Channels): Connected to {redis_url}")
            return True
        else:
            print("❌ Redis (Channels): Channel layer not configured")
            return False
    except Exception as e:
        print(f"❌ Redis (Channels): Connection failed - {e}")
        return False


def main():
    """Run all checks."""
    print("Checking infrastructure connectivity...\n")
    
    results = []
    results.append(("PostgreSQL", check_postgresql()))
    results.append(("Redis (Celery)", check_redis_celery()))
    results.append(("Redis (Channels)", check_redis_channels()))
    
    print("\n" + "="*50)
    all_ok = all(result[1] for result in results)
    
    if all_ok:
        print("✅ All infrastructure services are accessible!")
        return 0
    else:
        print("❌ Some infrastructure services are not accessible.")
        print("\nMake sure docker-compose services are running:")
        print("  cd infrastructure && docker-compose up -d")
        return 1


if __name__ == '__main__':
    sys.exit(main())

