#!/usr/bin/env python
"""
Script to test retry and cancel functionality for ImageTasks.

This script helps simulate different scenarios:
1. Create a job with multiple image tasks
2. Simulate stuck tasks (RUNNING with 0% progress)
3. Simulate failed tasks
4. Test cancel and retry endpoints

Usage:
    python scripts/test_retry_cancel.py
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

from django.contrib.auth import get_user_model
from apps.jobs.models import Job, ImageTask
from apps.datasets.models import Dataset
from apps.jobs.tasks import generate_image_task
from apps.audit.helpers import emit_event
import json

User = get_user_model()

def create_test_dataset():
    """Create a minimal test dataset."""
    # Try to get existing dataset or create new one
    try:
        dataset = Dataset.objects.first()
        if dataset:
            return dataset
    except:
        pass
    
    # Create new dataset with required fields
    import tempfile
    import os
    
    # Create a temporary file for storage_path
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.write('{"test": "data"}')
    temp_file.close()
    
    dataset = Dataset.objects.create(
        source_type='espacenet_excel',
        normalized_format='json',
        storage_path=temp_file.name,
        summary_stats={'rows': 3, 'columns': 3},
        columns_map={}
    )
    return dataset

def create_test_job_with_tasks():
    """Create a test job with multiple image tasks in different states."""
    print("\n" + "=" * 60)
    print("Creating test job with multiple image tasks...")
    print("=" * 60)
    
    # Get or create a test user
    user, _ = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Create test dataset
    dataset = create_test_dataset()
    
    # Create job
    job = Job.objects.create(
        created_by=user,
        dataset=dataset,
        status=Job.Status.RUNNING,
        progress_total=0
    )
    
    print(f"[OK] Created Job ID: {job.id}")
    
    # Create image tasks in different states
    tasks = []
    
    # 1. SUCCESS task
    success_task = ImageTask.objects.create(
        job=job,
        algorithm_key='top_patent_countries',
        algorithm_version='1.0',
        status=ImageTask.Status.SUCCESS,
        progress=100
    )
    tasks.append(('SUCCESS', success_task))
    print(f"  [OK] Created SUCCESS task: {success_task.id}")
    
    # 2. FAILED task
    failed_task = ImageTask.objects.create(
        job=job,
        algorithm_key='top_patent_applicants',
        algorithm_version='1.0',
        status=ImageTask.Status.FAILED,
        progress=0,
        error_code='TEST_ERROR',
        error_message='Simulated failure for testing'
    )
    tasks.append(('FAILED', failed_task))
    print(f"  [OK] Created FAILED task: {failed_task.id}")
    
    # 3. RUNNING task (simulating stuck task)
    running_task = ImageTask.objects.create(
        job=job,
        algorithm_key='patent_trends_cumulative',
        algorithm_version='1.0',
        status=ImageTask.Status.RUNNING,
        progress=0  # Stuck at 0%
    )
    tasks.append(('RUNNING (stuck)', running_task))
    print(f"  [OK] Created RUNNING (stuck) task: {running_task.id}")
    
    # 4. PENDING task
    pending_task = ImageTask.objects.create(
        job=job,
        algorithm_key='patent_evolution',
        algorithm_version='1.0',
        status=ImageTask.Status.PENDING,
        progress=0
    )
    tasks.append(('PENDING', pending_task))
    print(f"  [OK] Created PENDING task: {pending_task.id}")
    
    # 5. CANCELLED task
    cancelled_task = ImageTask.objects.create(
        job=job,
        algorithm_key='cpc_treemap',
        algorithm_version='1.0',
        status=ImageTask.Status.CANCELLED,
        progress=0
    )
    tasks.append(('CANCELLED', cancelled_task))
    print(f"  [OK] Created CANCELLED task: {cancelled_task.id}")
    
    return job, tasks

def test_cancel_endpoint(task_id):
    """Test the cancel endpoint."""
    print(f"\n[TEST] Testing CANCEL endpoint for task {task_id}...")
    
    import requests
    from django.conf import settings
    
    url = f"http://localhost:8000/api/image-tasks/{task_id}/cancel/"
    
    try:
        response = requests.post(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] Cancel successful: {data.get('message')}")
            print(f"     New status: {data.get('status')}")
            return True
        else:
            print(f"  [ERROR] Cancel failed: {response.status_code}")
            print(f"     Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  [WARNING] Could not connect to API: {e}")
        print(f"     Make sure Django server is running on port 8000")
        return False

def test_retry_endpoint(task_id):
    """Test the retry endpoint."""
    print(f"\n[TEST] Testing RETRY endpoint for task {task_id}...")
    
    import requests
    from django.conf import settings
    
    url = f"http://localhost:8000/api/image-tasks/{task_id}/retry/"
    
    try:
        response = requests.post(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] Retry successful: {data.get('message')}")
            print(f"     New status: {data.get('status')}")
            return True
        else:
            print(f"  [ERROR] Retry failed: {response.status_code}")
            print(f"     Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  [WARNING] Could not connect to API: {e}")
        print(f"     Make sure Django server is running on port 8000")
        return False

def test_direct_model_operations():
    """Test cancel and retry operations directly on models."""
    print("\n" + "=" * 60)
    print("Testing direct model operations...")
    print("=" * 60)
    
    job, tasks = create_test_job_with_tasks()
    
    # Test canceling a RUNNING task
    running_task = next(t for state, t in tasks if state == 'RUNNING (stuck)')
    print(f"\n1. Testing CANCEL on RUNNING task {running_task.id}...")
    running_task.status = ImageTask.Status.CANCELLED
    running_task.save()
    print(f"   [OK] Task {running_task.id} cancelled successfully")
    
    # Refresh from DB
    running_task.refresh_from_db()
    if running_task.status == ImageTask.Status.CANCELLED:
        print(f"   [OK] Status confirmed: {running_task.status}")
    else:
        print(f"   [ERROR] Status mismatch: expected CANCELLED, got {running_task.status}")
    
    # Test retrying a FAILED task
    failed_task = next(t for state, t in tasks if state == 'FAILED')
    print(f"\n2. Testing RETRY on FAILED task {failed_task.id}...")
    failed_task.status = ImageTask.Status.PENDING
    failed_task.progress = 0
    failed_task.error_code = None
    failed_task.error_message = None
    failed_task.save()
    print(f"   [OK] Task {failed_task.id} reset to PENDING")
    
    # Refresh from DB
    failed_task.refresh_from_db()
    if failed_task.status == ImageTask.Status.PENDING:
        print(f"   [OK] Status confirmed: {failed_task.status}")
        print(f"   [OK] Error cleared: error_code={failed_task.error_code}, error_message={failed_task.error_message}")
    else:
        print(f"   [ERROR] Status mismatch: expected PENDING, got {failed_task.status}")
    
    # Test retrying a CANCELLED task
    cancelled_task = next(t for state, t in tasks if state == 'CANCELLED')
    print(f"\n3. Testing RETRY on CANCELLED task {cancelled_task.id}...")
    cancelled_task.status = ImageTask.Status.PENDING
    cancelled_task.progress = 0
    cancelled_task.save()
    print(f"   [OK] Task {cancelled_task.id} reset to PENDING")
    
    # Refresh from DB
    cancelled_task.refresh_from_db()
    if cancelled_task.status == ImageTask.Status.PENDING:
        print(f"   [OK] Status confirmed: {cancelled_task.status}")
    else:
        print(f"   [ERROR] Status mismatch: expected PENDING, got {cancelled_task.status}")
    
    print(f"\n[OK] All direct model operations completed")
    print(f"\n[INFO] Test Job ID: {job.id}")
    print(f"   You can view this job in the frontend at: http://localhost:3000/jobs/{job.id}")
    
    return job, tasks

def main():
    """Main test function."""
    import sys
    
    print("\n" + "=" * 60)
    print("  ImageTask Retry & Cancel Test Script")
    print("=" * 60)
    
    print("\nThis script will:")
    print("  1. Create a test job with tasks in different states")
    print("  2. Test cancel and retry operations")
    print("  3. Verify status changes")
    
    # Allow command line argument or interactive input
    if len(sys.argv) > 1:
        choice = sys.argv[1].strip()
    else:
        try:
            choice = input("\nChoose test mode:\n  1. Direct model operations (no API)\n  2. API endpoint tests (requires server)\n  3. Both\n\nEnter choice (1-3): ").strip()
        except (EOFError, KeyboardInterrupt):
            # If running non-interactively, default to option 1
            print("\n[WARNING] Running non-interactively, defaulting to option 1 (Direct model operations)")
            choice = "1"
    
    if choice == '1' or choice == '3':
        job, tasks = test_direct_model_operations()
    
    if choice == '2' or choice == '3':
        print("\n" + "=" * 60)
        print("Testing API endpoints...")
        print("=" * 60)
        print("\n[WARNING] Make sure Django server is running: python manage.py runserver")
        try:
            input("\nPress Enter to continue...")
        except (EOFError, KeyboardInterrupt):
            print("\n[Skipping] API tests require interactive input")
            return
        
        job, tasks = create_test_job_with_tasks()
        
        # Test cancel on RUNNING task
        running_task = next(t for state, t in tasks if state == 'RUNNING (stuck)')
        test_cancel_endpoint(running_task.id)
        
        # Test retry on FAILED task
        failed_task = next(t for state, t in tasks if state == 'FAILED')
        test_retry_endpoint(failed_task.id)
        
        # Test retry on CANCELLED task
        cancelled_task = next(t for state, t in tasks if state == 'CANCELLED')
        test_retry_endpoint(cancelled_task.id)
        
        print(f"\n[INFO] Test Job ID: {job.id}")
        print(f"   You can view this job in the frontend at: http://localhost:3000/jobs/{job.id}")
    
    print("\n" + "=" * 60)
    print("  Test Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Open the frontend and navigate to the job")
    print("  2. Verify that buttons appear correctly:")
    print("     - Cancel button on RUNNING/PENDING tasks")
    print("     - Retry button on FAILED/RUNNING/PENDING/CANCELLED tasks")
    print("  3. Test the buttons in the UI")
    print("  4. Check WebSocket updates in real-time")

if __name__ == '__main__':
    main()
