# 🚀 Быстрый старт на Render.com (5 минут)

## 1️⃣ Отправьте код на GitHub

```bash
cd /home/batyr/projects/erp-system
git add .
git commit -m "feat: Add Render.com deployment configuration"
git push origin main
```

## 2️⃣ Создайте аккаунт на Render

1. Зайдите на https://render.com
2. Sign Up через GitHub
3. Подключите аккаунт `bridgecoresystems-cmd`

## 3️⃣ Деплой через Blueprint

1. В Render Dashboard: **New** → **Blueprint**
2. Выберите репозиторий: `bridgecoresystems-cmd/erp-system`
3. Render найдет `render.yaml`
4. Нажмите **Apply**

**Render создаст автоматически:**
- ✅ PostgreSQL database
- ✅ Redis instance
- ✅ Web Service с Django + WebSocket

## 4️⃣ Добавьте Environment Variables

В настройках Web Service (`erp-system`) добавьте:

### Генерируем SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Добавьте переменные:
- `SECRET_KEY` = [сгенерированный ключ]
- `DEBUG` = `False`
- `DJANGO_SETTINGS_MODULE` = `factory_erp.settings_production`
- `WEB_CONCURRENCY` = `2`

*(DATABASE_URL и REDIS_URL добавятся автоматически)*

## 5️⃣ Деплой!

1. Нажмите **Manual Deploy** (или подождите auto-deploy)
2. Дождитесь "✅ Live" статуса (3-5 минут)
3. Откройте ваш URL: `https://erp-system.onrender.com`

## 6️⃣ Первый вход

- URL: `https://erp-system.onrender.com/login/`
- Username: `admin`
- Password: `changeme123`

**⚠️ Сразу смените пароль в админке!**

## 7️⃣ Настройте ESP32

В коде ESP32 измените URL:
```cpp
const char* server_url = "https://erp-system.onrender.com";
```

---

## Готово! 🎉

Ваша ERP система работает 24/7 в интернете!

**Полная документация**: см. `RENDER_DEPLOYMENT_GUIDE.md`

