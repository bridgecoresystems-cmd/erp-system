# settings.py
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-factory-erp-2024-secure-key-change-in-production-now'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*',
    '192.168.1.101',
    
]  # замените на ваш IP
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',  # Установлен
    'crispy_forms',
    'django_tables2',  # Установлен
    'django_extensions',  # Установлен
    'admin_interface',  # Установлен
    'mptt',  # Установлен
    'simple_history',  # Установлен
    'import_export',
    'corsheaders',
    'colorfield',  # Установлен
    'channels',  # WebSocket support
    'channels_redis',  # Redis backend for channels
    'employees',
    'security',  # Теперь с openpyxl
    'django_celery_beat',  # Установлен
    'lohia_monitor',  # Мониторинг станка Lohia
    
]

MIDDLEWARE = [
     'corsheaders.middleware.CorsMiddleware',  # Не установлен
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {  # Не установлен
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

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'factory_erp_db',
        'USER': 'erp_user',
        'PASSWORD': 'erp_password123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
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
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Ashgabat'  # Время Туркменистана
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (uploaded images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки для загрузки изображений
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB

# Настройки админки
ADMIN_SITE_HEADER = "Заводская ERP Система"
ADMIN_SITE_TITLE = "Панель управления"
ADMIN_INDEX_TITLE = "Добро пожаловать в ERP систему"

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
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'employees': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# ==== НАСТРОЙКИ АУТЕНТИФИКАЦИИ ====
LOGIN_URL = '/login/'  # Куда перенаправлять неавторизованных пользователей
LOGIN_REDIRECT_URL = '/employees/'  # Куда перенаправлять после входа
LOGOUT_REDIRECT_URL = '/login/'  # Куда перенаправлять после выхода

# Время жизни сессии (необязательно)
SESSION_COOKIE_AGE = 86400  # 24 часа в секундах
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Не закрывать сессию при закрытии браузера
SESSION_SAVE_EVERY_REQUEST = True  # Обновлять время жизни при каждом запросе

# Дополнительные настройки для предотвращения SessionInterrupted
SESSION_COOKIE_SECURE = False  # Для разработки
SESSION_COOKIE_HTTPONLY = True  # Защита от XSS
SESSION_COOKIE_SAMESITE = 'Lax'  # Защита от CSRF
SESSION_ENGINE = 'django.contrib.sessions.backends.file'  # Использовать файлы для сессий
SESSION_FILE_PATH = '/tmp/django_sessions'  # Путь для файлов сессий

# WebSocket Configuration
ASGI_APPLICATION = 'factory_erp.asgi.application'

# Channel Layers Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# WebSocket Settings
WEBSOCKET_URL = '/ws/'
WEBSOCKET_RECONNECT_DELAY = 3  # seconds
WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 5

