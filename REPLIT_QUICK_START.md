# 🚀 Replit - Быстрый старт (15 минут)

## ✅ Преимущества: 100% бесплатно, без кредитной карты, с WebSocket!

---

## Шаг 1: Создайте БД (5 минут)

### PostgreSQL на Neon.tech (бесплатно)
1. https://neon.tech → Sign up через GitHub
2. **Create project** → Name: `erp-database`
3. 📝 Скопируйте **Pooled connection URL**:
   ```
   postgresql://user:pass@host.neon.tech/neondb?sslmode=require
   ```

### Redis на Upstash (бесплатно)
1. https://upstash.com → Sign up через GitHub
2. **Create database** → Name: `erp-redis`, Region: EU-Central
3. 📝 Скопируйте **UPSTASH_REDIS_REST_URL**:
   ```
   rediss://default:xxx@host.upstash.io:6379
   ```

---

## Шаг 2: Импорт в Replit (2 минуты)

1. https://replit.com → Sign up через GitHub
2. **Create Repl** → **Import from GitHub**
3. URL: `https://github.com/bridgecoresystems-cmd/erp-system`
4. Нажмите **Import from GitHub**

---

## Шаг 3: Настройка Secrets (3 минуты)

В Replit откройте **🔒 Secrets** (левая панель) и добавьте:

### Генерируйте SECRET_KEY:
В Shell (внизу):
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Добавьте по одному:
- `SECRET_KEY` = [сгенерированный ключ]
- `DEBUG` = `False`
- `DJANGO_SETTINGS_MODULE` = `factory_erp.settings_replit`
- `DATABASE_URL` = [URL из Neon]
- `REDIS_URL` = [URL из Upstash]

---

## Шаг 4: Установка и настройка (5 минут)

В Shell (внизу экрана):

```bash
# Установка зависимостей
pip install -r requirements.txt

# Переход в Django проект
cd factory_erp

# Миграции БД
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com  
# Password: [ваш пароль]

# Создание групп
python manage.py create_master_group
python manage.py create_lohia_groups

# Сборка статики
python manage.py collectstatic --no-input
```

---

## Шаг 5: Запуск! 🚀

1. Нажмите зеленую кнопку **Run** вверху
2. Дождитесь: `Listening on TCP address 0.0.0.0:8000`
3. Откройте ваш URL: `https://your-repl.replit.app`

---

## Шаг 6: Проверка

1. Откройте `/login/`
2. Войдите с учетными данными admin
3. Проверьте WebSocket в консоли браузера (F12)

---

## 💡 Важно: Держим приложение активным

Replit засыпает после неактивности. Решение:

### UptimeRobot (бесплатно)
1. https://uptimerobot.com → Sign up
2. **Add Monitor**:
   - Type: HTTP(s)
   - URL: ваш Replit URL
   - Interval: 5 minutes
3. Сохранить

Теперь приложение всегда активно! ✅

---

## 🔧 ESP32 настройка

В коде ESP32:
```cpp
const char* server_url = "https://your-repl.replit.app";
```

---

## 🐛 Если что-то не работает:

1. **Application error**: проверьте все Secrets добавлены
2. **DB error**: убедитесь `?sslmode=require` в DATABASE_URL
3. **Static files**: запустите `python manage.py collectstatic`
4. **WebSocket error**: проверьте REDIS_URL формат `rediss://`

---

## ✅ Готово!

Ваша ERP система работает 24/7 бесплатно! 🎉

**Полная документация**: `REPLIT_DEPLOYMENT_GUIDE.md`

