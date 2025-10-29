"""
Django settings for PythonAnywhere deployment
"""

from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
# Замените на уникальный ключ! Можно сгенерировать через:
# python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'ЗАМЕНИТЕ_НА_СВОЙ_СЕКРЕТНЫЙ_КЛЮЧ_ИЗ_ПЕРЕМЕННЫХ_ОКРУЖЕНИЯ')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Замените на ваш домен PythonAnywhere
ALLOWED_HOSTS = [
    'yourusername.pythonanywhere.com',
    '127.0.0.1',
    'localhost',
]

# Database
# SQLite для бесплатного tier PythonAnywhere
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings для production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = False  # Только если используете HTTPS
CSRF_COOKIE_SECURE = False  # Только если используете HTTPS

# Logging для production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'error.log'),
            'formatter': 'verbose'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'employees': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'lohia_monitor': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'security': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Создать директорию для логов если её нет
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Email settings (опционально, для уведомлений об ошибках)
# ADMINS = [('Your Name', 'your.email@example.com')]
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')

print("✅ PythonAnywhere settings loaded")
print(f"📁 BASE_DIR: {BASE_DIR}")
print(f"🗄️  Database: SQLite at {DATABASES['default']['NAME']}")
print(f"📦 STATIC_ROOT: {STATIC_ROOT}")
print(f"🎨 MEDIA_ROOT: {MEDIA_ROOT}")

