"""
Testing settings for the Intelli project.

These settings are used when running tests.
Optimized for speed and isolation.
"""

from .base import *

# Use a faster in-memory database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
# Set to True if you need to test migrations
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

# Uncomment to disable migrations during tests
# MIGRATION_MODULES = DisableMigrations()

# Password hashers - use faster algorithm for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests (optional - comment out if you need test logs)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Email backend - use in-memory backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# CORS - allow all origins in tests (for testing purposes)
CORS_ALLOW_ALL_ORIGINS = True

# Cache - use dummy cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable security features for faster tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Use faster session backend
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# Static files - don't collect in tests
STATIC_ROOT = None

# Media files - use temporary directory
import tempfile
MEDIA_ROOT = tempfile.mkdtemp()

# Django REST Framework - simplified for tests
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# Test-specific settings
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Disable debug toolbar and other development tools if present
DEBUG = False

# Allowed hosts for tests
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

