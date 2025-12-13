"""
Config package initialization.
Imports Celery app to ensure tasks are discovered.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)

