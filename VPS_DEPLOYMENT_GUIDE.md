# 🚀 Полное руководство по деплою ERP системы на VPS Ubuntu 24

## 📋 Что будет установлено:

- ✅ **Python 3.11** - основной язык
- ✅ **PostgreSQL 16** - база данных
- ✅ **Redis** - для WebSocket и Celery
- ✅ **Nginx** - веб-сервер и reverse proxy
- ✅ **Daphne** - ASGI сервер для WebSocket
- ✅ **Supervisor** - управление процессами
- ✅ **Certbot** - SSL сертификаты (опционально)

---

## 🖥️ Характеристики VPS:

**Hostinger KVM 1:**
- CPU: 1 vCore
- RAM: 4GB
- Storage: 50GB NVMe
- OS: Ubuntu 24.04 LTS
- Достаточно для: 10-20 одновременных пользователей + ESP32 устройства

---

## 1️⃣ Подключение к VPS

### SSH подключение:

```bash
ssh root@your-vps-ip
# Введите пароль который выслал Hostinger
```

### Создание нового пользователя (рекомендуется):

```bash
# Создаем пользователя
adduser deploy
usermod -aG sudo deploy

# Настраиваем SSH для нового пользователя
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Переключаемся на нового пользователя
su - deploy
```

---

## 2️⃣ Обновление системы и установка базовых пакетов

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    nginx \
    supervisor \
    redis-server \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    certbot \
    python3-certbot-nginx \
    ufw \
    htop \
    curl \
    vim

# Проверка версий
python3 --version  # Должно быть Python 3.11.x
psql --version        # PostgreSQL 16.x
redis-cli --version   # Redis 7.x
nginx -v              # nginx/1.24.x
```

---

## 3️⃣ Настройка PostgreSQL

### Создание базы данных и пользователя:

```bash
# Переключаемся на пользователя postgres
sudo -u postgres psql

# В PostgreSQL консоли:
```

```sql
-- Создание пользователя
CREATE USER erp_user WITH PASSWORD 'ВСТАВЬ_СЮДА_СЛОЖНЫЙ_ПАРОЛЬ';

-- Создание базы данных
CREATE DATABASE factory_erp_db OWNER erp_user;

-- Права доступа
GRANT ALL PRIVILEGES ON DATABASE factory_erp_db TO erp_user;
ALTER USER erp_user CREATEDB;  -- Для тестовой БД

-- Выход
\q
```

```bash
# Проверка подключения
psql -U erp_user -d factory_erp_db -h localhost
# Введите пароль
# Если подключилось - успешно! Выход: \q
```

### Настройка PostgreSQL для удаленного доступа (опционально):

```bash
sudo nano /etc/postgresql/16/main/postgresql.conf
# Найти строку: #listen_addresses = 'localhost'
# Изменить на: listen_addresses = '*'

sudo nano /etc/postgresql/16/main/pg_hba.conf
# Добавить в конец:
# host    all             all             0.0.0.0/0            md5

# Перезапуск
sudo systemctl restart postgresql
```

---

## 4️⃣ Настройка Redis

```bash
# Проверка запуска
sudo systemctl status redis-server

# Если не запущен
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Тестирование
redis-cli ping
# Должен ответить: PONG
```

### Настройка Redis (опционально):

```bash
sudo nano /etc/redis/redis.conf

# Найти и изменить:
# maxmemory 256mb
# maxmemory-policy allkeys-lru

# Перезапуск
sudo systemctl restart redis-server
```

---

## 5️⃣ Клонирование проекта

```bash
# Переход в домашнюю директорию
cd ~

# Клонирование (замени на свой репозиторий)
git clone https://github.com/bridgecoresystems-cmd/erp-system.git
cd erp-system

# Переключение на ветку с WebSocket
git checkout websocket-postgres

# Проверка
git branch
# Должно быть: * websocket-postgres
```

---

## 6️⃣ Настройка виртуального окружения

```bash
# Создание venv
cd ~/erp-system
python3 -m venv venv

# Активация
source venv/bin/activate

# Обновление pip
pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Проверка
pip list | grep -i django
# Должно показать Django 4.2.x или выше
```

---

## 7️⃣ Настройка Django settings для production

### Создание production settings:

```bash
cd ~/erp-system/factory_erp/factory_erp
nano settings_production.py
```

Вставьте:

```python
from .settings import *
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'СГЕНЕРИРУЙ_НОВЫЙ_КЛЮЧ')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Замените на ваш домен или IP
ALLOWED_HOSTS = [
    'erp.bridgecore.tech',
    'www.erp.bridgecore.tech',
    '148.230.81.243',
    'localhost',
    '127.0.0.1',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'factory_erp_db',
        'USER': 'erp_user',
        'PASSWORD': os.environ.get('DB_PASSWORD', 'Kepler03lim@'),
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # Переиспользование соединений
    }
}

# Redis для channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True  # Если используете HTTPS
SESSION_COOKIE_SECURE = True  # Если используете HTTPS
SECURE_SSL_REDIRECT = False  # Поставить True после настройки SSL

# CORS (если нужно)
CORS_ALLOWED_ORIGINS = [
    "https://erp.bridgecore.tech",
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
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
    },
}

# Создать директорию для логов
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
```

Сохранить: `Ctrl+X → Y → Enter`

---

## 8️⃣ Применение миграций и сбор статики

```bash
cd ~/erp-system/factory_erp
source ../venv/bin/activate

# Применение миграций
python manage.py migrate --settings=factory_erp.settings_production

# Создание суперпользователя
python manage.py createsuperuser --settings=factory_erp.settings_production

# Сбор статических файлов
python manage.py collectstatic --noinput --settings=factory_erp.settings_production

# Проверка
python manage.py check --settings=factory_erp.settings_production --deploy
```

---

## 9️⃣ Настройка Supervisor для Daphne и Celery

### Создание конфигурации Daphne:

```bash
sudo nano /etc/supervisor/conf.d/daphne.conf
```

Вставьте:

```ini
[program:daphne]
directory=/home/deploy/erp-system/factory_erp
command=/home/deploy/erp-system/venv/bin/daphne -u /run/daphne/daphne.sock factory_erp.asgi:application
user=deploy
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/deploy/erp-system/logs/daphne.log
environment=DJANGO_SETTINGS_MODULE="factory_erp.settings_production"

[program:celery]
directory=/home/deploy/erp-system/factory_erp
command=/home/deploy/erp-system/venv/bin/celery -A factory_erp worker -l info
user=deploy
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/deploy/erp-system/logs/celery.log
environment=DJANGO_SETTINGS_MODULE="factory_erp.settings_production"

[program:celery-beat]
directory=/home/deploy/erp-system/factory_erp
command=/home/deploy/erp-system/venv/bin/celery -A factory_erp beat -l info
user=deploy
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/deploy/erp-system/logs/celery-beat.log
environment=DJANGO_SETTINGS_MODULE="factory_erp.settings_production"
```

### Создание директории для socket:

```bash
sudo mkdir -p /run/daphne
sudo chown deploy:deploy /run/daphne

# Создание логов
mkdir -p ~/erp-system/logs
```

### Перезагрузка Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status

# Должно быть:
# daphne                           RUNNING   pid 12345, uptime 0:00:05
# celery                           RUNNING   pid 12346, uptime 0:00:05
# celery-beat                      RUNNING   pid 12347, uptime 0:00:05
```

---

## 🔟 Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/erp-system
```

Вставьте:

```nginx
upstream daphne {
    server unix:/run/daphne/daphne.sock fail_timeout=0;
}

server {
    listen 80;
    server_name erp.bridgecore.tech www.erp.bridgecore.tech 148.230.81.243;

    client_max_body_size 10M;

    # Статические файлы
    location /static/ {
        alias /home/deploy/erp-system/factory_erp/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Медиа файлы
    location /media/ {
        alias /home/deploy/erp-system/factory_erp/media/;
        expires 7d;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Все остальные запросы
    location / {
        proxy_pass http://daphne;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### Активация конфигурации:

```bash
# Создание символической ссылки
sudo ln -s /etc/nginx/sites-available/erp-system /etc/nginx/sites-enabled/

# Удаление default конфигурации
sudo rm /etc/nginx/sites-enabled/default

# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 1️⃣1️⃣ Настройка Firewall

```bash
# Включение UFW
sudo ufw enable

# Разрешить SSH
sudo ufw allow 22/tcp

# Разрешить HTTP и HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Статус
sudo ufw status

# Должно быть:
# 22/tcp        ALLOW       Anywhere
# 80/tcp        ALLOW       Anywhere
# 443/tcp       ALLOW       Anywhere
```

---

## 1️⃣2️⃣ Настройка SSL (HTTPS) с Let's Encrypt

```bash
# Получение сертификата
sudo certbot --nginx -d erp.bridgecore.tech -d www.erp.bridgecore.tech

# Следуйте инструкциям:
# 1. Введите email
# 2. Согласитесь с условиями
# 3. Выберите опцию redirect (2)

# Автоматическое обновление
sudo certbot renew --dry-run

# Проверка
sudo systemctl status certbot.timer
```

### После получения SSL обновите settings_production.py:

```python
# settings_production.py
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 год
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## 1️⃣3️⃣ Переменные окружения (рекомендуется)

```bash
nano ~/.bashrc
```

Добавьте в конец:

```bash
# Django production settings
export DJANGO_SETTINGS_MODULE=factory_erp.settings_production
export DJANGO_SECRET_KEY='ВАШ_СЕКРЕТНЫЙ_КЛЮЧ'
export DB_PASSWORD='ВАШ_ПАРОЛЬ_БД'
```

```bash
source ~/.bashrc
```

---

## 1️⃣4️⃣ Проверка деплоя

### 1. Проверка процессов:

```bash
sudo supervisorctl status
# Все должны быть RUNNING
```

### 2. Проверка логов:

```bash
# Daphne
tail -f ~/erp-system/logs/daphne.log

# Celery
tail -f ~/erp-system/logs/celery.log

# Nginx
sudo tail -f /var/log/nginx/error.log
```

### 3. Проверка сайта:

Откройте в браузере:
- `http://148.230.81.243/` или `https://erp.bridgecore.tech/`
- `/admin/` - админка должна работать
- Проверьте WebSocket в DevTools → Network → WS

---

## 1️⃣5️⃣ Обновление кода

Когда нужно обновить код на сервере:

```bash
cd ~/erp-system

# Pull изменений
git pull origin websocket-postgres

# Активация venv
source venv/bin/activate

# Установка новых зависимостей (если есть)
pip install -r requirements.txt

# Применение миграций
cd factory_erp
python manage.py migrate --settings=factory_erp.settings_production

# Сбор статики
python manage.py collectstatic --noinput --settings=factory_erp.settings_production

# Перезапуск всех сервисов
sudo supervisorctl restart all

# Проверка
sudo supervisorctl status
```

---

## 🔧 Устранение неполадок

### WebSocket не подключается:

```bash
# Проверка Daphne
sudo supervisorctl status daphne

# Логи
tail -f ~/erp-system/logs/daphne.log

# Перезапуск
sudo supervisorctl restart daphne
```

### Ошибка 502 Bad Gateway:

```bash
# Проверка socket файла
ls -la /run/daphne/

# Права доступа
sudo chown deploy:www-data /run/daphne/daphne.sock

# Перезапуск
sudo supervisorctl restart daphne
sudo systemctl restart nginx
```

### База данных не подключается:

```bash
# Проверка PostgreSQL
sudo systemctl status postgresql

# Проверка подключения
psql -U erp_user -d factory_erp_db -h localhost

# Логи PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

---

## 📊 Мониторинг

### Использование ресурсов:

```bash
# CPU и RAM
htop

# Дисковое пространство
df -h

# Процессы
ps aux | grep -E 'daphne|celery|nginx'
```

### Логи:

```bash
# Все логи Supervisor
sudo tail -f /var/log/supervisor/supervisord.log

# Системные логи
sudo journalctl -xe
```

---

## 🎉 Готово!

Ваша ERP система развернута на VPS с:
- ✅ WebSocket для real-time обновлений
- ✅ PostgreSQL для надежного хранения данных
- ✅ Redis для кэширования и WebSocket
- ✅ Nginx для production
- ✅ SSL сертификаты
- ✅ Автоматический запуск при перезагрузке

### Доступ:

- **Сайт:** `https://erp.bridgecore.tech` или `http://148.230.81.243`
- **Админка:** `https://erp.bridgecore.tech/admin/`
- **API для ESP32:** `https://erp.bridgecore.tech/employees/api/rfid-scan/`

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `~/erp-system/logs/`
2. Проверьте статус сервисов: `sudo supervisorctl status`
3. Проверьте Nginx: `sudo nginx -t`
4. Проверьте firewall: `sudo ufw status`

