# 🚀 Деплой ERP системы на Replit (100% бесплатно, без карты)

## ✅ Преимущества Replit:
- Полностью бесплатный, БЕЗ кредитной карты
- Поддержка WebSocket (real-time обновления работают!)
- PostgreSQL через бесплатный Neon.tech
- Redis через Upstash (бесплатно)
- Простой деплой через GitHub

---

## Шаг 1: Создание аккаунта Replit

1. Зайдите на https://replit.com
2. Нажмите **Sign up**
3. Войдите через GitHub (используйте аккаунт `bridgecoresystems-cmd`)
4. Подтвердите email

---

## Шаг 2: Создание бесплатной PostgreSQL БД на Neon.tech

### 2.1. Регистрация на Neon
1. Зайдите на https://neon.tech
2. **Sign up** → войдите через GitHub
3. Бесплатный план: 0.5 GB storage, никаких карт не нужно!

### 2.2. Создание базы данных
1. В Neon Dashboard нажмите **Create a project**
2. **Name**: `erp-database`
3. **PostgreSQL version**: 15 (latest)
4. **Region**: Frankfurt (ближе к вам)
5. Нажмите **Create project**

### 2.3. Получение connection string
1. В проекте перейдите на **Dashboard**
2. Найдите **Connection string**
3. Скопируйте **Pooled connection** (важно!)
   ```
   postgresql://user:password@ep-xxxxx.eu-central-1.aws.neon.tech/neondb?sslmode=require
   ```
4. 📝 **Сохраните этот URL** - понадобится позже

---

## Шаг 3: Создание бесплатного Redis на Upstash

### 3.1. Регистрация на Upstash
1. Зайдите на https://upstash.com
2. **Sign up** → войдите через GitHub
3. Бесплатный план: 10k commands/day

### 3.2. Создание Redis базы
1. В Upstash Dashboard нажмите **Create database**
2. **Name**: `erp-redis`
3. **Type**: Regional
4. **Region**: EU-Central (Frankfurt)
5. **TLS**: Enabled
6. Нажмите **Create**

### 3.3. Получение connection string
1. Откройте созданную базу
2. Прокрутите до **Redis URL**
3. Скопируйте **UPSTASH_REDIS_REST_URL**:
   ```
   rediss://default:xxx@eu1-grateful-xxx.upstash.io:6379
   ```
4. 📝 **Сохраните** - понадобится позже

---

## Шаг 4: Импорт проекта в Replit

### 4.1. Создание Repl
1. В Replit Dashboard нажмите **Create Repl**
2. Выберите **Import from GitHub**
3. В URL вставьте:
   ```
    
   ```
4. **Name**: `erp-system`
5. **Language**: Python (автоматически определится)
6. Нажмите **Import from GitHub**

### 4.2. Подождите импорта
Replit склонирует весь репозиторий (может занять 1-2 минуты)

---

## Шаг 5: Создание конфигурационных файлов для Replit

### 5.1. Создайте файл `.replit` (в корне проекта)

В Replit редакторе создайте файл `.replit`:

```toml
run = "cd factory_erp && python manage.py migrate && daphne -b 0.0.0.0 -p 8000 factory_erp.asgi:application"

[nix]
channel = "stable-23_11"

[deployment]
run = ["sh", "-c", "cd factory_erp && python manage.py migrate && daphne -b 0.0.0.0 -p 8000 factory_erp.asgi:application"]
deploymentTarget = "cloudrun"

[env]
PYTHONUNBUFFERED = "1"
DJANGO_SETTINGS_MODULE = "factory_erp.settings_replit"
```

### 5.2. Создайте `replit.nix` (в корне проекта)

```nix
{ pkgs }: {
  deps = [
    pkgs.postgresql
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
  ];
}
```

### 5.3. Создайте `factory_erp/factory_erp/settings_replit.py`

```python
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
```

---

## Шаг 6: Настройка Secrets (Environment Variables)

В Replit есть встроенное хранилище секретов:

### 6.1. Откройте Secrets
1. В левой панели Replit нажмите на **🔒 Secrets** (иконка замка)
2. Или через **Tools** → **Secrets**

### 6.2. Добавьте секреты (по одному):

**Сгенерируйте SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Добавьте переменные:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | [сгенерированный ключ] |
| `DEBUG` | `False` |
| `DJANGO_SETTINGS_MODULE` | `factory_erp.settings_replit` |
| `DATABASE_URL` | [URL из Neon.tech] |
| `REDIS_URL` | [URL из Upstash] |

**Пример DATABASE_URL:**
```
postgresql://user:password@ep-xxxxx.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

**Пример REDIS_URL:**
```
rediss://default:xxx@eu1-grateful-xxx.upstash.io:6379
```

---

## Шаг 7: Установка зависимостей и запуск

### 7.1. Откройте Shell в Replit
В нижней части экрана есть **Shell** (терминал)

### 7.2. Установите зависимости
```bash
cd factory_erp
pip install -r ../requirements.txt
```

### 7.3. Соберите статику
```bash
python manage.py collectstatic --no-input
```

### 7.4. Выполните миграции
```bash
python manage.py migrate
```

### 7.5. Создайте суперпользователя
```bash
python manage.py createsuperuser
```
- Username: `admin`
- Email: `admin@example.com`
- Password: (введите свой пароль)

### 7.6. Создайте группы пользователей
```bash
python manage.py create_master_group
python manage.py create_lohia_groups
```

---

## Шаг 8: Запуск приложения

### 8.1. Нажмите кнопку **Run** (зеленая кнопка вверху)

Replit запустит:
```bash
daphne -b 0.0.0.0 -p 8000 factory_erp.asgi:application
```

### 8.2. Дождитесь запуска
Вы увидите в консоли:
```
Starting ASGI/Daphne version ...
Listening on TCP address 0.0.0.0:8000
```

### 8.3. Откройте приложение
Replit откроет встроенный браузер справа, или нажмите кнопку **Open in new tab** 🔗

**Ваш URL будет:**
```
https://erp-system.yourusername.replit.app
```

---

## Шаг 9: Первый вход

1. Откройте ваше приложение
2. Перейдите на `/login/`
3. Войдите с учетными данными суперпользователя

---

## Шаг 10: Настройка ESP32 для Replit

В коде ESP32 измените URL:

```cpp
// ESP32 настройки для Replit
const char* server_url = "https://erp-system.yourusername.replit.app";
const char* esp32_id = "LOHIA-001";

// API endpoints
const char* pulse_endpoint = "/api/lohia/pulse/";
const char* rfid_endpoint = "/api/lohia/rfid/";
```

---

## ⚠️ Важные особенности Replit Free Plan:

### Ограничения:
- **Спящий режим**: приложение засыпает после неактивности
- **Первый запрос медленный**: ~10-20 секунд для пробуждения
- **Ресурсы**: 0.5 vCPU, 512 MB RAM
- **Always On**: не доступен на Free плане

### Решения:
1. **UptimeRobot** - пинговать каждые 5 минут (держит активным):
   - Зарегистрируйтесь на https://uptimerobot.com (бесплатно)
   - Добавьте монитор: ваш Replit URL
   - Интервал: 5 минут

2. **Cron-job.org** - альтернатива UptimeRobot

---

## 🐛 Troubleshooting

### Проблема 1: "Application error"
**Решение:**
1. Проверьте консоль (Shell) на ошибки
2. Убедитесь что все Secrets добавлены
3. Проверьте `DATABASE_URL` и `REDIS_URL`

### Проблема 2: "Static files not loading"
**Решение:**
```bash
cd factory_erp
python manage.py collectstatic --no-input
```

### Проблема 3: "Database connection error"
**Решение:**
1. Проверьте что в `DATABASE_URL` есть `?sslmode=require`
2. Убедитесь что Neon database активна
3. Проверьте connection string в Neon Dashboard

### Проблема 4: "WebSocket disconnected"
**Решение:**
1. Проверьте `REDIS_URL` в Secrets
2. Убедитесь что Upstash Redis активен
3. Проверьте формат: `rediss://` (с двумя 's')

### Проблема 5: Приложение постоянно "засыпает"
**Решение:**
- Настройте UptimeRobot (см. выше)
- Или перейдите на Replit Hacker Plan ($7/месяц для Always On)

---

## 📊 Мониторинг

### Просмотр логов в реальном времени:
В Replit Shell:
```bash
cd factory_erp
python manage.py runserver  # для просмотра Django логов
```

### Проверка соединений:
```bash
# PostgreSQL
python manage.py dbshell

# Redis
redis-cli -u $REDIS_URL ping
```

---

## 🔄 Обновление приложения

После изменений в GitHub:

### Вариант 1: Автоматическое обновление
Replit автоматически синхронизируется с GitHub при рестарте

### Вариант 2: Ручное обновление
В Shell:
```bash
git pull origin main
pip install -r requirements.txt
cd factory_erp
python manage.py migrate
python manage.py collectstatic --no-input
```

Затем нажмите **Stop** и **Run**

---

## 🎯 Итоговая структура

```
erp-system/
├── .replit                          # Конфигурация запуска
├── replit.nix                       # Системные зависимости
├── requirements.txt                 # Python зависимости
├── factory_erp/
│   ├── manage.py
│   ├── factory_erp/
│   │   ├── settings.py             # Локальные настройки
│   │   ├── settings_replit.py      # Production для Replit
│   │   ├── asgi.py                 # WebSocket support
│   │   └── ...
│   └── ...
└── ...
```

---

## ✅ Checklist перед запуском

- [ ] Аккаунт Replit создан
- [ ] PostgreSQL на Neon.tech создана
- [ ] Redis на Upstash создан
- [ ] Проект импортирован из GitHub
- [ ] Файлы `.replit` и `replit.nix` созданы
- [ ] `settings_replit.py` создан
- [ ] Все Secrets добавлены
- [ ] Зависимости установлены
- [ ] Миграции выполнены
- [ ] Суперпользователь создан
- [ ] Статика собрана
- [ ] Приложение запущено

---

## 🚀 Готово!

Ваша ERP система работает на Replit:
```
https://erp-system.yourusername.replit.app
```

**100% бесплатно, без кредитной карты!** ✨

---

## 💡 Советы по оптимизации

1. **Используйте UptimeRobot** - держит приложение активным
2. **Оптимизируйте статику** - используйте CDN для больших файлов
3. **Кэшируйте запросы** - используйте Redis для кэширования
4. **Мониторьте ресурсы** - следите за использованием RAM

---

**Нужна помощь?** Replit имеет отличное сообщество на форумах! 😊

