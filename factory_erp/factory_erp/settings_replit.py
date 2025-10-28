"""
Settings for Replit deployment
"""
import os
import dj_database_url
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-replit-secrets')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Allowed hosts
ALLOWED_HOSTS = [
    '.replit.dev',
    '.replit.app',
    '.repl.co',
    'localhost',
    '127.0.0.1',
]

# Get Repl info
REPL_SLUG = os.environ.get('REPL_SLUG', '')
REPL_OWNER = os.environ.get('REPL_OWNER', '')
if REPL_SLUG and REPL_OWNER:
    ALLOWED_HOSTS.append(f'{REPL_SLUG}.{REPL_OWNER}.repl.co')
    ALLOWED_HOSTS.append(f'{REPL_SLUG}-{REPL_OWNER}.replit.app')

# Application definition
INSTALLED_APPS = [
    'daphne',  # WebSocket support
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'crispy_forms',
    'django_tables2',
    'django_extensions',
    'admin_interface',
    'mptt',
    'simple_history',
    'import_export',
    'corsheaders',
    'colorfield',
    'channels',
    'channels_redis',
    'employees',
    'security',
    'django_celery_beat',
    'lohia_monitor',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'lohia_monitor.middleware.MasterRedirectMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

ROOT_URLCONF = 'factory_erp.urls'

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

WSGI_APPLICATION = 'factory_erp.wsgi.application'
ASGI_APPLICATION = 'factory_erp.asgi.application'

# Database - Neon PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    # Fallback для локальной разработки
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Ashgabat'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Admin settings
ADMIN_SITE_HEADER = "Заводская ERP Система"
ADMIN_SITE_TITLE = "Панель управления"
ADMIN_INDEX_TITLE = "Добро пожаловать в ERP систему"

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Authentication
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/employees/'
LOGOUT_REDIRECT_URL = '/login/'

# Session settings
SESSION_COOKIE_AGE = 86400
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    'https://*.replit.dev',
    'https://*.replit.app',
    'https://*.repl.co',
]

# Channel Layers - Upstash Redis
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# WebSocket Settings
WEBSOCKET_URL = '/ws/'
WEBSOCKET_RECONNECT_DELAY = 3
WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 5

# CORS
CORS_ALLOW_ALL_ORIGINS = True  # Для Replit
CORS_ALLOW_CREDENTIALS = True

# Security settings for production
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False  # Replit handles SSL
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

