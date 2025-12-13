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
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Change to IsAuthenticated in production
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
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
    },
}

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Task Routes
CELERY_TASK_ROUTES = {
    'apps.ingestion.*': {'queue': 'ingestion_io'},
    'apps.jobs.tasks.generate_image_task': {'queue': 'charts_cpu'},
    'apps.jobs.tasks.run_job': {'queue': 'charts_cpu'},
    'apps.jobs.tasks.finalize_job': {'queue': 'charts_cpu'},
    'apps.ai_descriptions.*': {'queue': 'ai'},
}

# Celery Task Queues (using kombu.Queue format)
from kombu import Queue

CELERY_TASK_QUEUES = (
    Queue('ingestion_io'),
    Queue('charts_cpu'),
    Queue('ai'),
)

# Celery Task Annotations
CELERY_TASK_ANNOTATIONS = {
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
    },
}

# Celery Broker Transport Options
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 180,
}

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

