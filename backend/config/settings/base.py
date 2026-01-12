"""
Base settings for the Intelli project.

These settings are shared across all environments (development, production, testing).
Environment-specific settings should be defined in their respective files.
"""

from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    'channels',
    # Local apps
    'apps.core',
    'apps.authentication',
    'apps.ingestion',
    'apps.datasets',
    'apps.algorithms',
    'apps.jobs',
    'apps.artifacts',
    'apps.ai_descriptions',
    'apps.audit',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware should be near the top
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = config('LANGUAGE_CODE', default='en-us')
TIME_ZONE = config('TIME_ZONE', default='UTC')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/6.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework configuration
# NOTE: DEFAULT_PERMISSION_CLASSES is set per environment (development.py / production.py)
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [],  # Override in environment-specific settings
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Custom SessionAuthentication that only enforces CSRF on mutating methods
        # This fixes 403 errors on GET requests when CSRF token isn't fetched yet
        'apps.authentication.authentication.CsrfExemptSessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# CORS Configuration
# These are base settings - environment-specific files will override CORS_ALLOWED_ORIGINS
CORS_ALLOW_CREDENTIALS = config('CORS_ALLOW_CREDENTIALS', default=True, cast=bool)
CORS_ALLOW_ALL_ORIGINS = False  # Never allow all origins in production

# CSRF Configuration
# Session cookie is HttpOnly by default in Django (SESSION_COOKIE_HTTPONLY = True)
# CSRF cookie must be readable by JavaScript to send X-CSRFToken header
CSRF_COOKIE_HTTPONLY = False  # Allow JS to read csrftoken cookie
CSRF_COOKIE_SAMESITE = 'Lax'  # Works for same-site and cross-site with credentials

# Microsoft OAuth2 Configuration (Azure AD / Entra ID)
# These must be set in environment variables
MICROSOFT_CLIENT_ID = config('MICROSOFT_CLIENT_ID', default='')
MICROSOFT_CLIENT_SECRET = config('MICROSOFT_CLIENT_SECRET', default='')
MICROSOFT_TENANT_ID = config('MICROSOFT_TENANT_ID', default='common')  # 'common' for multi-tenant
MICROSOFT_REDIRECT_URI = config('MICROSOFT_REDIRECT_URI', default='http://localhost:8000/api/auth/microsoft/callback/')
MICROSOFT_LOGIN_REDIRECT_URL = config('MICROSOFT_LOGIN_REDIRECT_URL', default='http://localhost:3000/en/dashboard')
MICROSOFT_LOGIN_ERROR_URL = config('MICROSOFT_LOGIN_ERROR_URL', default='http://localhost:3000/en/login')
MICROSOFT_SCOPES = ['openid', 'profile', 'email', 'User.Read']

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Celery Configuration
# NOTE: Task routes, annotations, and queues are configured in config/celery.py
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Django Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [config('REDIS_URL', default='redis://localhost:6379/1')],
        },
    },
}

# drf-spectacular settings for OpenAPI/Swagger documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Intelli API',
    'DESCRIPTION': 'API para generación de gráficos y análisis de datos de patentes',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'TAGS': [
        {'name': 'Jobs', 'description': 'Operaciones relacionadas con trabajos de generación de gráficos'},
        {'name': 'Image Tasks', 'description': 'Tareas de generación de imágenes de gráficos'},
        {'name': 'Description Tasks', 'description': 'Tareas de generación de descripciones con IA'},
        {'name': 'AI', 'description': 'Operaciones relacionadas con inteligencia artificial'},
        {'name': 'Health', 'description': 'Endpoints de verificación de salud del sistema'},
    ],
    'CONTACT': {
        'name': 'Intelli Team',
    },
    'LICENSE': {
        'name': 'Proprietary',
    },
    'EXTENSIONS_INFO': {
        'x-logo': {
            'url': 'https://via.placeholder.com/200x50.png?text=Intelli',
        }
    },
}

# Database Connection Retry Configuration
# =======================================
# Configuration for automatic retry with exponential backoff on database
# connection failures. This follows the industry-standard retry pattern
# with jitter to prevent thundering herd issues.
#
# The retry formula is:
#   delay = min(MAX_DELAY, INITIAL_DELAY * (EXPONENTIAL_BASE ** attempt))
#   delay = delay ± (delay * JITTER_FACTOR)  # if JITTER is True
#
# Default configuration will retry 5 times with delays of:
#   Attempt 1: ~0.1s, Attempt 2: ~0.2s, Attempt 3: ~0.4s,
#   Attempt 4: ~0.8s, Attempt 5: ~1.6s (total max: ~3.1s)
#
# Environment Variables:
#   DB_RETRY_MAX_ATTEMPTS: Maximum retry attempts (default: 5)
#   DB_RETRY_INITIAL_DELAY: Initial delay in seconds (default: 0.1)
#   DB_RETRY_MAX_DELAY: Maximum delay cap in seconds (default: 30)
#
DATABASE_RETRY_CONFIG = {
    'MAX_ATTEMPTS': config('DB_RETRY_MAX_ATTEMPTS', default=5, cast=int),
    'INITIAL_DELAY': config('DB_RETRY_INITIAL_DELAY', default=0.1, cast=float),
    'MAX_DELAY': config('DB_RETRY_MAX_DELAY', default=30.0, cast=float),
    'EXPONENTIAL_BASE': config('DB_RETRY_EXPONENTIAL_BASE', default=2.0, cast=float),
    'JITTER': config('DB_RETRY_JITTER', default=True, cast=bool),
    'JITTER_FACTOR': config('DB_RETRY_JITTER_FACTOR', default=0.1, cast=float),
}

