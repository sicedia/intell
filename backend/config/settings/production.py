"""
Production settings for the Intelli project.

These settings are used in production deployment.
IMPORTANT: Never commit sensitive values to version control!
"""

from .base import *
from decouple import config
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# Allowed hosts - MUST be set in production
ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# Database configuration
# Use DATABASE_URL environment variable (recommended for production)
# Automatically uses retry-enabled backends for PostgreSQL
DATABASE_URL = config('DATABASE_URL')
db_config = dj_database_url.parse(DATABASE_URL, conn_max_age=600)

# Replace PostgreSQL backend with retry-enabled version
# dj_database_url uses 'django.db.backends.postgresql' or 'postgresql://' URLs
engine = db_config.get('ENGINE', '')
if 'postgresql' in engine or 'postgres' in engine:
    db_config['ENGINE'] = 'apps.core.db.backends.postgresql'

DATABASES = {
    'default': db_config
}

# Email configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

# CORS Configuration for production
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS').split(',')
CORS_ALLOW_CREDENTIALS = config('CORS_ALLOW_CREDENTIALS', default=True, cast=bool)
CORS_ALLOW_ALL_ORIGINS = False  # Never allow all origins in production

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Additional Security Headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# CSRF Protection
# CSRF cookie must be readable by JavaScript to send X-CSRFToken header
# Note: base.py sets CSRF_COOKIE_HTTPONLY = False, but we need to ensure it's False in production
CSRF_COOKIE_HTTPONLY = False  # Allow JS to read csrftoken cookie
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='').split(',') if config('CSRF_TRUSTED_ORIGINS', default='') else []

# Session Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Proxy SSL Header (required when behind reverse proxy like nginx)
# Tells Django to trust X-Forwarded-Proto header from the proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HTTPS Settings (uncomment when SSL is configured)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)

# Static files - must be collected and served by web server in production
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Use STORAGES instead of deprecated STATICFILES_STORAGE (Django 4.2+)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

# Media files - configure for production storage (S3, etc.)
MEDIA_ROOT = BASE_DIR / 'media'

# Logging - production configuration
LOGGING['handlers']['file']['filename'] = BASE_DIR / 'logs' / 'django_production.log'
LOGGING['root']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['django.request']['level'] = 'ERROR'

# Remove console handler in production (use file handler only)
LOGGING['root']['handlers'] = ['file']
LOGGING['loggers']['django']['handlers'] = ['file']
LOGGING['loggers']['django.request']['handlers'] = ['file']

# Django REST Framework - production settings
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',  # Only JSON in production
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # Require authentication
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Anonymous users: 100 requests per hour
        'user': '1000/hour',  # Authenticated users: 1000 requests per hour
    },
    # Exempt health check endpoints from throttling
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# Custom throttle rates for specific endpoints (can be overridden in views)
# Health check endpoints should not be throttled
REST_FRAMEWORK_THROTTLE_EXEMPT = [
    'apps.core.views.health_check',
    'apps.core.views.redis_health_check',
    'apps.core.views.celery_health_check',
    'apps.core.views.database_health_check',
]

# Cache configuration - Use Redis for better performance
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        # Note: Django 6.0+ native Redis backend doesn't use CLIENT_CLASS
        # That option is only for django-redis package
        'KEY_PREFIX': 'intell',
        'TIMEOUT': 300,  # 5 minutes default timeout
    }
}

# Session configuration - Use cached_db for better performance
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Production-specific middleware additions
MIDDLEWARE.insert(1, 'django.middleware.security.SecurityMiddleware')

# Admin URL protection (optional)
# ADMIN_URL = config('ADMIN_URL', default='admin/')

