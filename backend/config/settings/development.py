"""
Development settings for the Intelli project.

These settings are used during local development.
"""

from .base import *
from decouple import config
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Database configuration
# Supports both SQLite (default) and PostgreSQL (via docker-compose)
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Use PostgreSQL if DATABASE_URL is provided
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    # Default to SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    # Alternatively, use PostgreSQL from docker-compose.yml
    # Uncomment the following to use PostgreSQL:
    # DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.postgresql',
    #         'NAME': config('POSTGRES_DB', default='intell'),
    #         'USER': config('POSTGRES_USER', default='intell_user'),
    #         'PASSWORD': config('POSTGRES_PASSWORD', default='patents2026$'),
    #         'HOST': config('POSTGRES_HOST', default='localhost'),
    #         'PORT': config('POSTGRES_PORT', default='5432'),
    #     }
    # }

# Email backend - use console for development
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

# CORS Configuration for development
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000'
).split(',')

CORS_ALLOW_CREDENTIALS = config('CORS_ALLOW_CREDENTIALS', default=True, cast=bool)

# Allow all origins in development (for easier frontend development)
# Remove this in production!
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)

# CSRF Configuration for cross-origin requests in development
# Required because frontend (localhost:3000) and backend (localhost:8000) are different origins
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000'
).split(',')

# Django REST Framework - enable browsable API and AllowAny in development
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Only for development
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Enable browsable API
    ],
}

# Logging - reduced verbosity in development
LOGGING['root']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Static files - Django will serve these in development
# No need to run collectstatic in development

# Media files
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_ROOT.mkdir(exist_ok=True)

# Development-specific settings
# SQL queries logging disabled to reduce console output
# Uncomment the following if you need to debug SQL queries:
# if DEBUG:
#     LOGGING['loggers']['django.db.backends'] = {
#         'handlers': ['console'],
#         'level': 'DEBUG',
#         'propagate': False,
#     }

# Celery Configuration
# ===================
# For true async task processing, disable EAGER mode and run Celery workers:
#   celery -A config worker -l info -Q ingestion_io,charts_cpu,ai
# Or run all queues:
#   celery -A config worker -l info
#
# To run Celery workers in development:
#   1. Ensure Redis is running (docker-compose up redis)
#   2. Start worker: celery -A config worker -l info -Q ingestion_io,charts_cpu,ai
#   3. Optional: Start flower for monitoring: celery -A config flower
#
# EAGER mode (commented out below) runs tasks synchronously in the Django process.
# This is useful for debugging but defeats the async architecture.
# Uncomment these lines if you want synchronous execution for debugging:
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True

