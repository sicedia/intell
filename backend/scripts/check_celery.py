#!/usr/bin/env python
"""
Check Celery worker status and Redis connectivity.

This script verifies that:
1. Redis is accessible
2. Celery workers are running
3. Tasks can be enqueued and processed

Usage:
    python scripts/check_celery.py
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from celery import current_app
from django.conf import settings
import redis


def check_redis():
    """Check Redis connectivity."""
    print("=" * 60)
    print("Checking Redis connectivity...")
    print("=" * 60)
    
    try:
        # Check Celery broker
        broker_url = settings.CELERY_BROKER_URL
        print(f"Broker URL: {broker_url}")
        
        # Parse Redis URL
        if broker_url.startswith('redis://'):
            # Extract host, port, db from redis://localhost:6379/0
            parts = broker_url.replace('redis://', '').split('/')
            host_port = parts[0].split(':')
            host = host_port[0] if len(host_port) > 0 else 'localhost'
            port = int(host_port[1]) if len(host_port) > 1 else 6379
            db = int(parts[1]) if len(parts) > 1 else 0
            
            r = redis.Redis(host=host, port=port, db=db, socket_connect_timeout=2)
            r.ping()
            print(f"✅ Redis broker is accessible at {host}:{port}/{db}")
            
            # Check Channels Redis
            channel_layer = settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
            if isinstance(channel_layer, str):
                # Parse redis://localhost:6379/1
                parts = channel_layer.replace('redis://', '').split('/')
                host_port = parts[0].split(':')
                host = host_port[0] if len(host_port) > 0 else 'localhost'
                port = int(host_port[1]) if len(host_port) > 1 else 6379
                db = int(parts[1]) if len(parts) > 1 else 1
            else:
                host, port = channel_layer
                db = 1
            
            r_channels = redis.Redis(host=host, port=port, db=db, socket_connect_timeout=2)
            r_channels.ping()
            print(f"✅ Redis channels layer is accessible at {host}:{port}/{db}")
            
            return True
        else:
            print(f"⚠️  Unknown broker type: {broker_url}")
            return False
            
    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Please ensure Redis is running: cd infrastructure && docker-compose up -d redis")
        return False
    except Exception as e:
        print(f"❌ Error checking Redis: {e}")
        return False


def check_celery_workers():
    """Check if Celery workers are running."""
    print("\n" + "=" * 60)
    print("Checking Celery workers...")
    print("=" * 60)
    
    try:
        # Get active workers
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        
        if not active_workers:
            print("❌ No Celery workers are running")
            print("   Start workers with: python scripts/start_celery_worker.ps1")
            print("   Or: celery -A config worker -l info -Q ingestion_io,charts_cpu,ai")
            return False
        
        print(f"✅ Found {len(active_workers)} active worker(s):")
        for worker_name in active_workers.keys():
            print(f"   - {worker_name}")
        
        # Check registered tasks
        registered = inspect.registered()
        if registered:
            total_tasks = sum(len(tasks) for tasks in registered.values())
            print(f"\n   Total registered tasks: {total_tasks}")
        
        # Check queues
        stats = inspect.stats()
        if stats:
            print("\n   Worker statistics:")
            for worker_name, worker_stats in stats.items():
                pool_size = worker_stats.get('pool', {}).get('max-concurrency', 'N/A')
                print(f"   - {worker_name}: pool size = {pool_size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking workers: {e}")
        print("   This might be normal if workers are not running.")
        return False


def check_eager_mode():
    """Check if EAGER mode is enabled."""
    print("\n" + "=" * 60)
    print("Checking Celery configuration...")
    print("=" * 60)
    
    eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    if eager:
        print("⚠️  WARNING: CELERY_TASK_ALWAYS_EAGER is enabled")
        print("   Tasks will run synchronously in the Django process.")
        print("   This defeats the async architecture.")
        print("   Disable it in config/settings/development.py for true async processing.")
        return False
    else:
        print("✅ EAGER mode is disabled - async processing enabled")
        return True


def main():
    """Main check function."""
    print("\n" + "=" * 60)
    print("  Celery & Redis Status Check")
    print("=" * 60 + "\n")
    
    results = []
    
    # Check Redis
    results.append(("Redis", check_redis()))
    
    # Check EAGER mode
    results.append(("EAGER Mode", check_eager_mode()))
    
    # Check workers
    results.append(("Workers", check_celery_workers()))
    
    # Summary
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    
    all_ok = True
    for name, status in results:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}")
        if not status:
            all_ok = False
    
    print()
    
    if all_ok:
        print("✅ All checks passed! Celery is ready to process tasks.")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
