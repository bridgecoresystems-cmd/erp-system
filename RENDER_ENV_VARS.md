# Environment Variables for Render.com

Эти переменные окружения нужно настроить в Render.com Dashboard:

## Обязательные переменные (автоматически устанавливаются Render):

- `DATABASE_URL` - автоматически из PostgreSQL service
- `REDIS_URL` - автоматически из Redis service
- `RENDER_EXTERNAL_HOSTNAME` - автоматически устанавливается Render

## Переменные которые нужно добавить вручную:

### Django Settings
```
SECRET_KEY = [Generate new secret key]
DEBUG = False
DJANGO_SETTINGS_MODULE = factory_erp.settings_production
WEB_CONCURRENCY = 2
```

### Как сгенерировать SECRET_KEY:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### ALLOWED_HOSTS (опционально)
```
ALLOWED_HOSTS = your-app.onrender.com,www.your-domain.com
```

## Опциональные переменные:

### CORS (если нужен API доступ с других доменов)
```
CORS_ALLOWED_ORIGINS = https://example.com,https://another-domain.com
```

### Sentry (для отслеживания ошибок)
```
SENTRY_DSN = https://your-sentry-dsn@sentry.io/project-id
```

### Celery (если используете фоновые задачи)
```
CELERY_BROKER_URL = redis://...
CELERY_RESULT_BACKEND = redis://...
```

## Пример команды для генерации SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

