# 🔧 Static Files Fix - ASGI Server

## ❌ **Проблема:**
CSS и другие статические файлы не загружались при использовании Daphne (ASGI сервер) вместо обычного Django development server.

## ✅ **Решение:**
Добавлен `ASGIStaticFilesHandler` в `factory_erp/asgi.py` для обслуживания статических файлов.

## 🔧 **Что было изменено:**

### **Файл:** `factory_erp/asgi.py`

**До:**
```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factory_erp.settings')

django_asgi_app = get_asgi_application()

from factory_erp.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
```

**После:**
```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factory_erp.settings')

django_asgi_app = get_asgi_application()

from factory_erp.routing import websocket_urlpatterns

# Wrap Django ASGI app with static files handler
django_asgi_app = ASGIStaticFilesHandler(django_asgi_app)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
```

## 🚀 **Как запустить сервер:**

### **Правильная команда:**
```bash
cd /home/batyr/projects/erp-system/factory_erp
source ../venv/bin/activate
daphne -b 0.0.0.0 -p 8000 factory_erp.asgi:application
```

### **Проверка:**
1. **Страница:** `http://localhost:8000/lohia/dashboard/`
2. **CSS файл:** `http://localhost:8000/static/css/style.css`
3. **Статус:** Оба должны возвращать HTTP 200

## 🔍 **Почему это произошло:**

### **Django Development Server:**
- ✅ Автоматически обслуживает статические файлы
- ✅ Поддерживает только HTTP (не WebSocket)
- ❌ Не подходит для WebSocket

### **Daphne (ASGI Server):**
- ✅ Поддерживает WebSocket
- ❌ Не обслуживает статические файлы автоматически
- ✅ Требует `ASGIStaticFilesHandler`

## 📋 **Альтернативные решения:**

### **1. Использовать WhiteNoise (Production):**
```python
# settings.py
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... другие middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### **2. Nginx для статических файлов (Production):**
```nginx
location /static/ {
    alias /path/to/staticfiles/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### **3. Отдельный сервер для статики:**
```bash
# В отдельном терминале
python manage.py runserver 8001 --insecure
```

## ✅ **Результат:**
- ✅ CSS файлы загружаются корректно
- ✅ WebSocket работает
- ✅ Все статические файлы доступны
- ✅ Страницы отображаются правильно

---

**🎉 Проблема решена! Теперь и WebSocket, и статические файлы работают корректно.**
