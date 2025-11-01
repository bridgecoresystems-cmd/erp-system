"""
Django Production Settings for VPS Deployment
Hostinger KVM 1 - Ubuntu 24.04
"""

from .settings import *
import os

# ===== SECURITY =====

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'f3h@$&4f27ht_loe!3&-c8c#$6ea=mi!w_&8xl49f(s5nmc!xh')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allowed hosts - ваш домен и IP
ALLOWED_HOSTS = [
    'erp.bridgecore.tech',
    'www.erp.bridgecore.tech',
    '148.230.81.243',
    'localhost',
    '127.0.0.1',
]

# ===== DATABASE =====

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'factory_erp_db',
        'USER': 'erp_user',
        'PASSWORD': os.environ.get('DB_PASSWORD', 'Kepler03lim@'),
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # Переиспользование соединений (10 минут)
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# ===== CHANNELS & WEBSOCKET =====

ASGI_APPLICATION = 'factory_erp.asgi.application'

# Redis для WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
            "capacity": 1500,  # Количество сообщений в канале
            "expiry": 10,  # Время жизни сообщений (секунды)
        },
    },
}

# WebSocket Settings
WEBSOCKET_URL = '/ws/'
WEBSOCKET_RECONNECT_DELAY = 3  # seconds
WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 5

# ===== STATIC & MEDIA FILES =====

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ===== SECURITY SETTINGS =====

# SSL/HTTPS (включить после настройки Certbot)
SECURE_SSL_REDIRECT = False  # Поставить True после настройки SSL
SESSION_COOKIE_SECURE = False  # Поставить True после SSL
CSRF_COOKIE_SECURE = False  # Поставить True после SSL

# Остальные security настройки
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 0  # Поставить 31536000 после SSL
SECURE_HSTS_INCLUDE_SUBDOMAINS = False  # Поставить True после SSL
SECURE_HSTS_PRELOAD = False  # Поставить True после SSL

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 часа
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# CSRF settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# ===== CORS (для ESP32 API) =====

CORS_ALLOWED_ORIGINS = [
    "http://erp.bridgecore.tech",
    "https://erp.bridgecore.tech",
    "http://148.230.81.243",
]

CORS_ALLOW_CREDENTIALS = True

# ===== LOGGING =====

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
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'daphne_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'daphne.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'celery.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'daphne': {
            'handlers': ['daphne_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['celery_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'employees': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'lohia_monitor': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'security': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Создать директорию для логов если её нет
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# ===== CELERY (для фоновых задач) =====

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Ashgabat'

# ===== EMAIL (опционально, для уведомлений) =====

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_USER', 'your-email@gmail.com')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your-app-password')
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ===== ADMIN =====

ADMINS = [
    ('Admin', 'admin@bridgecore.tech'),
]

MANAGERS = ADMINS

# ===== PERFORMANCE =====

# Кэширование (опционально)
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

# ===== DEBUG INFO =====

print("=" * 80)
print("✅ PRODUCTION SETTINGS LOADED")
print("=" * 80)
print(f"📍 DEBUG: {DEBUG}")
print(f"🌐 ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"🗄️  DATABASE: PostgreSQL - {DATABASES['default']['NAME']}@{DATABASES['default']['HOST']}")
print(f"📡 CHANNEL_LAYERS: Redis - {CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]}")
print(f"📁 STATIC_ROOT: {STATIC_ROOT}")
print(f"📁 MEDIA_ROOT: {MEDIA_ROOT}")
print(f"📁 LOGS_DIR: {LOGS_DIR}")
print(f"🔐 CSRF_COOKIE_SECURE: {CSRF_COOKIE_SECURE} (будет True после SSL)")
print(f"🔐 SESSION_COOKIE_SECURE: {SESSION_COOKIE_SECURE} (будет True после SSL)")
print("=" * 80)
