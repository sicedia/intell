"""
Celery configuration for Intelli project.
"""
import os
import sys
from celery import Celery
from django.conf import settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('config')

# Load settings from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Windows compatibility: Use 'solo' pool instead of 'prefork'
# The 'prefork' pool (default on Linux/macOS) doesn't work well on Windows
# due to how Windows handles process forking.
# In production (Linux), 'prefork' is used by default for better performance.
if sys.platform == 'win32':
    app.conf.worker_pool = 'solo'
    # Note: 'solo' pool runs tasks sequentially in the main thread
    # For better performance on Windows, consider using WSL2 or Docker
else:
    # Linux/macOS: Use 'prefork' pool by default (better performance, parallel execution)
    # This is the default, but we set it explicitly for clarity
    app.conf.worker_pool = 'prefork'

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Task routes - map tasks to queues
app.conf.task_routes = {
    'apps.ingestion.*': {'queue': 'ingestion_io'},
    'apps.jobs.tasks.generate_image_task': {'queue': 'charts_cpu'},
    'apps.jobs.tasks.run_job': {'queue': 'charts_cpu'},
    'apps.jobs.tasks.finalize_job': {'queue': 'charts_cpu'},
    'apps.ai_descriptions.*': {'queue': 'ai'},
}

# Task annotations - tuning per queue
app.conf.task_annotations = {
    'apps.ingestion.*': {
        'time_limit': 60,
        'soft_time_limit': 50,
        'acks_late': False,
    },
    'apps.jobs.tasks.generate_image_task': {
        'time_limit': 120,
        'soft_time_limit': 100,
        'acks_late': True,
    },
    'apps.jobs.tasks.run_job': {
        'time_limit': 120,
        'soft_time_limit': 100,
        'acks_late': True,
    },
    'apps.jobs.tasks.finalize_job': {
        'time_limit': 60,
        'soft_time_limit': 50,
        'acks_late': True,
    },
    'apps.ai_descriptions.*': {
        'time_limit': 60,
        'soft_time_limit': 50,
        'acks_late': True,
        'autoretry_for': (Exception,),
        'retry_backoff': True,
        'retry_backoff_max': 600,
        'retry_kwargs': {'max_retries': 3},
    },
}

# Task queues (using kombu.Queue format)
from kombu import Queue

app.conf.task_queues = (
    Queue('ingestion_io'),
    Queue('charts_cpu'),
    Queue('ai'),
)

# Broker transport options
app.conf.broker_transport_options = {
    'visibility_timeout': 180,  # >= time_limit más alto (120s)
}

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')

