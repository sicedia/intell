#!/usr/bin/env python
"""
Diagnose Celery configuration and common issues.

This script checks for common Celery problems and provides solutions.

Usage:
    python scripts/diagnose_celery.py
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

print("\n" + "=" * 60)
print("  Celery Diagnostics")
print("=" * 60 + "\n")

# Check 1: Django setup
print("1. Checking Django setup...")
try:
    import django
    django.setup()
    print("   ✅ Django setup successful")
except Exception as e:
    print(f"   ❌ Django setup failed: {e}")
    sys.exit(1)

# Check 2: Celery app import
print("\n2. Checking Celery app import...")
try:
    from config.celery import app
    print(f"   ✅ Celery app imported: {app.main}")
except Exception as e:
    print(f"   ❌ Failed to import Celery app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 3: Celery configuration
print("\n3. Checking Celery configuration...")
try:
    from django.conf import settings
    
    broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
    result_backend = getattr(settings, 'CELERY_RESULT_BACKEND', None)
    eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    
    print(f"   Broker URL: {broker_url}")
    print(f"   Result Backend: {result_backend}")
    print(f"   EAGER mode: {eager}")
    
    if eager:
        print("   ⚠️  WARNING: EAGER mode is enabled - tasks run synchronously")
    else:
        print("   ✅ EAGER mode disabled - async processing enabled")
        
except Exception as e:
    print(f"   ❌ Configuration check failed: {e}")

# Check 4: Redis connectivity
print("\n4. Checking Redis connectivity...")
try:
    import redis
    
    # Check broker
    broker_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
    if broker_url.startswith('redis://'):
        parts = broker_url.replace('redis://', '').split('/')
        host_port = parts[0].split(':')
        host = host_port[0] if len(host_port) > 0 else 'localhost'
        port = int(host_port[1]) if len(host_port) > 1 else 6379
        
        r = redis.Redis(host=host, port=port, db=0, socket_connect_timeout=2)
        r.ping()
        print(f"   ✅ Redis broker accessible at {host}:{port}/0")
    else:
        print(f"   ⚠️  Unknown broker type: {broker_url}")
        
except redis.ConnectionError as e:
    print(f"   ❌ Redis connection failed: {e}")
    print("   Solution: Start Redis with: cd infrastructure && docker-compose up -d redis")
except Exception as e:
    print(f"   ❌ Error checking Redis: {e}")

# Check 5: Task discovery
print("\n5. Checking task discovery...")
try:
    registered_tasks = list(app.tasks.keys())
    # Filter out built-in tasks
    user_tasks = [t for t in registered_tasks if not t.startswith('celery.')]
    
    print(f"   ✅ Found {len(user_tasks)} user-defined task(s):")
    for task in sorted(user_tasks)[:10]:  # Show first 10
        print(f"      - {task}")
    if len(user_tasks) > 10:
        print(f"      ... and {len(user_tasks) - 10} more")
        
except Exception as e:
    print(f"   ❌ Task discovery failed: {e}")
    import traceback
    traceback.print_exc()

# Check 6: Queue configuration
print("\n6. Checking queue configuration...")
try:
    queues = app.conf.task_queues
    print(f"   ✅ Configured {len(queues)} queue(s):")
    for queue in queues:
        print(f"      - {queue.name}")
        
    routes = app.conf.task_routes
    if routes:
        print(f"   ✅ Task routes configured: {len(routes)} route(s)")
        
except Exception as e:
    print(f"   ❌ Queue configuration check failed: {e}")

# Check 7: Common import issues
print("\n7. Checking for common import issues...")
issues_found = []

# Check if tasks are properly imported
try:
    from apps.jobs.tasks import generate_image_task, finalize_job
    print("   ✅ Job tasks imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import job tasks: {e}")
    issues_found.append(f"Import error: {e}")

# Check algorithm registry
try:
    from apps.algorithms.registry import AlgorithmRegistry
    registry = AlgorithmRegistry()
    algorithms = registry.list_algorithms()
    print(f"   ✅ Algorithm registry: {len(algorithms)} algorithm(s) registered")
except Exception as e:
    print(f"   ⚠️  Algorithm registry issue: {e}")
    issues_found.append(f"Algorithm registry: {e}")

# Check 8: Test task execution (if not eager)
print("\n8. Testing task execution...")
if not getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
    try:
        # Try to inspect active workers
        inspect = app.control.inspect()
        active = inspect.active()
        
        if active:
            print(f"   ✅ Found {len(active)} active worker(s)")
            for worker_name in active.keys():
                print(f"      - {worker_name}")
        else:
            print("   ⚠️  No active workers found")
            print("   Solution: Start worker with: celery -A config worker -l info")
            
    except Exception as e:
        print(f"   ⚠️  Could not check workers: {e}")
        print("   This is normal if workers are not running")
else:
    print("   ⚠️  EAGER mode enabled - skipping worker check")

# Summary
print("\n" + "=" * 60)
print("  Summary")
print("=" * 60)

if issues_found:
    print("\n⚠️  Issues found:")
    for issue in issues_found:
        print(f"   - {issue}")
    print("\nCommon solutions:")
    print("   1. Ensure Redis is running: docker-compose up -d redis")
    print("   2. Start Celery worker: celery -A config worker -l info")
    print("   3. Check Django settings: python manage.py check")
    print("   4. Verify imports: python manage.py shell")
else:
    print("\n✅ No obvious issues found!")
    print("\nIf you're still experiencing errors, please share:")
    print("   - The exact error message")
    print("   - When it occurs (startup, task execution, etc.)")
    print("   - Celery worker logs")

print()
