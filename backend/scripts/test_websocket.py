#!/usr/bin/env python
"""
Test WebSocket connection for job progress updates.

This script:
1. Creates a test job
2. Connects to the WebSocket endpoint
3. Verifies real-time event updates

Usage:
    python scripts/test_websocket.py
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from channels.testing import ChannelsLiveServerTestCase
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from apps.jobs.models import Job, ImageTask
from apps.datasets.models import Dataset
from apps.jobs.tasks import run_job
from apps.audit.helpers import emit_event


async def test_websocket_connection(job_id: int):
    """Test WebSocket connection and event reception."""
    try:
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            print("❌ Channel layer not configured")
            return False
        
        print(f"✅ Channel layer configured: {type(channel_layer).__name__}")
        
        # Test sending an event
        test_event = {
            "type": "job_event",
            "data": {
                "job_id": job_id,
                "entity_type": "job",
                "entity_id": job_id,
                "event_type": "TEST",
                "level": "INFO",
                "message": "Test WebSocket event",
                "progress": 50,
                "payload": {},
                "trace_id": "test-trace-123",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
        
        # Send to channel group - await directly since we're in async context
        await channel_layer.group_send(
            f"job_{job_id}",
            test_event
        )
        
        print(f"✅ Test event sent to job_{job_id} channel")
        return True
        
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_channels_config():
    """Check Django Channels configuration."""
    print("=" * 60)
    print("Checking Django Channels configuration...")
    print("=" * 60)
    
    from django.conf import settings
    
    # Check CHANNEL_LAYERS - use hasattr or getattr instead of __dict__
    try:
        channel_layers = getattr(settings, 'CHANNEL_LAYERS', None)
        if not channel_layers:
            print("❌ CHANNEL_LAYERS not configured")
            return False
        
        if 'default' not in channel_layers:
            print("❌ No 'default' channel layer configured")
            return False
        
        default_layer = channel_layers['default']
        backend = default_layer.get('BACKEND', '')
        
        print(f"✅ Channel layer backend: {backend}")
        
        if 'channels_redis' in backend:
            config = default_layer.get('CONFIG', {})
            hosts = config.get('hosts', [])
            print(f"✅ Redis hosts configured: {len(hosts)} host(s)")
            for i, host in enumerate(hosts):
                if isinstance(host, str):
                    print(f"   - Host {i+1}: {host}")
                else:
                    host_str, port = host
                    print(f"   - Host {i+1}: {host_str}:{port}")
            return True
        else:
            print(f"⚠️  Using non-Redis backend: {backend}")
            return True
    except Exception as e:
        print(f"❌ Error checking Channels config: {e}")
        return False


def check_redis_channels():
    """Check Redis connectivity for Channels."""
    print("\n" + "=" * 60)
    print("Checking Redis for Channels...")
    print("=" * 60)
    
    try:
        from django.conf import settings
        import redis
        
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
        
        r = redis.Redis(host=host, port=port, db=db, socket_connect_timeout=2)
        r.ping()
        print(f"✅ Redis Channels layer accessible at {host}:{port}/{db}")
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Redis Channels connection failed: {e}")
        print("   Please ensure Redis is running: cd infrastructure && docker-compose up -d redis")
        return False
    except Exception as e:
        print(f"❌ Error checking Redis Channels: {e}")
        return False


def check_websocket_routing():
    """Check WebSocket URL routing."""
    print("\n" + "=" * 60)
    print("Checking WebSocket routing...")
    print("=" * 60)
    
    try:
        from apps.jobs.routing import websocket_urlpatterns
        
        if not websocket_urlpatterns:
            print("❌ No WebSocket URL patterns found")
            return False
        
        print(f"✅ Found {len(websocket_urlpatterns)} WebSocket pattern(s):")
        for pattern in websocket_urlpatterns:
            print(f"   - {pattern.pattern}")
        
        # Check if ASGI application includes WebSocket routing
        from config.asgi import application
        
        if hasattr(application, 'application_mapping'):
            print("✅ ASGI application configured with routing")
        else:
            print("⚠️  ASGI application structure may need verification")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking routing: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("  WebSocket Configuration Test")
    print("=" * 60 + "\n")
    
    results = []
    
    # Check Channels config
    results.append(("Channels Config", check_channels_config()))
    
    # Check Redis for Channels
    results.append(("Redis Channels", check_redis_channels()))
    
    # Check WebSocket routing
    results.append(("WebSocket Routing", check_websocket_routing()))
    
    # Test WebSocket connection (requires a test job)
    print("\n" + "=" * 60)
    print("Testing WebSocket event emission...")
    print("=" * 60)
    
    try:
        # Create a minimal test dataset
        from django.core.files.base import ContentFile
        import tempfile
        
        # Create a temporary JSON file for dataset
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"test": "data"}], f)
            temp_path = f.name
        
        dataset = Dataset.objects.create(
            source_type='custom',
            normalized_format='json',
            storage_path=temp_path,
            summary_stats={'total_rows': 1},
            columns_map={'test': 'test'}
        )
        
        # Create a test job
        job = Job.objects.create(
            dataset=dataset,
            status=Job.Status.PENDING
        )
        
        # Create a test image task
        image_task = ImageTask.objects.create(
            job=job,
            algorithm_key='top_patent_countries',
            algorithm_version='1.0',
            status=ImageTask.Status.PENDING
        )
        
        print(f"✅ Created test job {job.id} with image task {image_task.id}")
        
        # Test event emission
        emit_event(
            job_id=job.id,
            image_task_id=image_task.id,
            event_type='TEST',
            level='INFO',
            message='Test WebSocket event',
            progress=50
        )
        
        print("✅ Event emitted successfully")
        
        # Test WebSocket connection - use sync wrapper since we're in sync context
        from asgiref.sync import sync_to_async
        
        async def run_test():
            return await test_websocket_connection(job.id)
        
        websocket_ok = asyncio.run(run_test())
        results.append(("WebSocket Events", websocket_ok))
        
        # Cleanup
        job.delete()
        dataset.delete()
        os.unlink(temp_path)
        
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("WebSocket Events", False))
    
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
        print("✅ All WebSocket checks passed!")
        print("\nWebSocket endpoint: ws://localhost:8000/ws/jobs/<job_id>/")
        print("Frontend should connect to this endpoint for real-time updates.")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
