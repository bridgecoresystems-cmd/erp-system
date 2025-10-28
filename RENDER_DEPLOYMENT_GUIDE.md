# 🚀 Полная инструкция по деплою ERP системы на Render.com

## Шаг 1: Подготовка репозитория (ВЫПОЛНЕНО ✅)

Все необходимые файлы уже созданы:
- ✅ `render.yaml` - конфигурация Blueprint для Render
- ✅ `build.sh` - скрипт сборки и миграций
- ✅ `requirements.txt` - обновлен с WebSocket зависимостями
- ✅ `factory_erp/factory_erp/settings_production.py` - production настройки

## Шаг 2: Отправка кода на GitHub

```bash
cd /home/batyr/projects/erp-system
git add .
git commit -m "feat: Add Render.com deployment configuration"
git push origin main
```

## Шаг 3: Создание аккаунта на Render.com

1. Перейдите на https://render.com
2. Нажмите **Sign Up**
3. Зарегистрируйтесь через GitHub (рекомендуется)
4. Подключите ваш GitHub аккаунт `bridgecoresystems-cmd`

## Шаг 4: Деплой через Blueprint

### Вариант A: Автоматический деплой через Blueprint (РЕКОМЕНДУЕТСЯ)

1. В Render Dashboard нажмите **New** → **Blueprint**
2. Выберите репозиторий `bridgecoresystems-cmd/erp-system`
3. Render автоматически обнаружит `render.yaml`
4. Нажмите **Apply**

Render создаст:
- ✅ PostgreSQL database (`erp-postgres`)
- ✅ Redis instance (`erp-redis`)
- ✅ Web Service (`erp-system`)

### Вариант B: Ручная настройка

Если Blueprint не работает, настройте вручную:

#### 4.1. Создайте PostgreSQL Database

1. **New** → **PostgreSQL**
2. **Name**: `erp-postgres`
3. **Database**: `factory_erp_db`
4. **User**: `erp_user`
5. **Region**: Frankfurt (ближе к вам)
6. **Plan**: Free
7. Нажмите **Create Database**
8. 📝 **Сохраните Internal Database URL**

#### 4.2. Создайте Redis Instance

1. **New** → **Redis**
2. **Name**: `erp-redis`
3. **Region**: Frankfurt
4. **Plan**: Free
5. Нажмите **Create Redis**
6. 📝 **Сохраните Internal Redis URL**

#### 4.3. Создайте Web Service

1. **New** → **Web Service**
2. Подключите репозиторий `bridgecoresystems-cmd/erp-system`
3. **Name**: `erp-system`
4. **Region**: Frankfurt
5. **Branch**: `main`
6. **Root Directory**: оставьте пустым
7. **Runtime**: Python 3
8. **Build Command**:
   ```bash
   ./build.sh
   ```
9. **Start Command**:
   ```bash
   cd factory_erp && daphne -b 0.0.0.0 -p $PORT factory_erp.asgi:application
   ```
10. **Plan**: Free

## Шаг 5: Настройка Environment Variables

В настройках Web Service добавьте переменные:

### Обязательные переменные:

1. **SECRET_KEY**
   ```
   Сгенерируйте новый ключ:
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Пример: `django-insecure-a8f7s9d8f7ads9f8ads7f89ads7f89ads7f`

2. **DEBUG**
   ```
   False
   ```

3. **DJANGO_SETTINGS_MODULE**
   ```
   factory_erp.settings_production
   ```

4. **DATABASE_URL**
   ```
   Вставьте Internal Database URL из PostgreSQL сервиса
   Пример: postgresql://user:password@dpg-xxxxx-a.frankfurt-postgres.render.com/factory_erp_db
   ```

5. **REDIS_URL**
   ```
   Вставьте Internal Redis URL из Redis сервиса
   Пример: redis://red-xxxxx-a.frankfurt-redis.render.com:6379
   ```

6. **WEB_CONCURRENCY**
   ```
   2
   ```

### Опциональные переменные:

7. **ALLOWED_HOSTS** (если нужен кастомный домен)
   ```
   your-domain.com,your-app.onrender.com
   ```

8. **SENTRY_DSN** (для отслеживания ошибок)
   ```
   https://your-sentry-dsn@sentry.io/project-id
   ```

## Шаг 6: Деплой!

1. Нажмите **Create Web Service** (или **Manual Deploy** если уже создан)
2. Render начнет сборку:
   - Установит зависимости из `requirements.txt`
   - Запустит `build.sh`:
     - Соберет статические файлы
     - Выполнит миграции БД
     - Создаст суперпользователя `admin` с паролем `changeme123`
   - Запустит Daphne сервер

3. Дождитесь **"Build succeeded"** и **"Live"** статуса

## Шаг 7: Проверка работы

1. Откройте URL вашего приложения:
   ```
   https://erp-system.onrender.com
   ```

2. Проверьте логин:
   - URL: `https://erp-system.onrender.com/login/`
   - Username: `admin`
   - Password: `changeme123`
   - **⚠️ СРАЗУ СМЕНИТЕ ПАРОЛЬ после первого входа!**

3. Проверьте админку:
   ```
   https://erp-system.onrender.com/admin/
   ```

4. Проверьте WebSocket:
   - Откройте браузерную консоль (F12)
   - Должно быть: `WebSocket connection established`

## Шаг 8: Настройка ESP32 для работы с Render

Обновите код ESP32:

```cpp
// ESP32 настройки для Render
const char* server_url = "https://erp-system.onrender.com";  // Ваш URL на Render
const char* esp32_id = "LOHIA-001";

// API endpoints
const char* api_endpoint = "/api/lohia/pulse/";  // Для импульсов
const char* rfid_endpoint = "/api/lohia/rfid/";  // Для RFID
```

## Шаг 9: Настройка кастомного домена (опционально)

1. В Render Dashboard → вашем Web Service → **Settings**
2. Scroll до **Custom Domain**
3. Добавьте ваш домен (например, `erp.yourcompany.com`)
4. Настройте DNS записи согласно инструкциям Render
5. Render автоматически получит SSL сертификат

## Шаг 10: Мониторинг и логи

### Просмотр логов:
1. В Render Dashboard → Web Service → **Logs**
2. Или через Render CLI:
   ```bash
   render logs -s erp-system
   ```

### Метрики:
- CPU usage
- Memory usage
- Request rate
- Response time

## Troubleshooting (Решение проблем)

### 1. Build Failed

**Проблема**: Ошибка при установке зависимостей
```bash
ERROR: Could not build wheels for ...
```

**Решение**: Проверьте `requirements.txt`, убедитесь что все пакеты совместимы

### 2. Application Error

**Проблема**: Сайт не открывается, 500 ошибка

**Решение**:
1. Проверьте логи в Render Dashboard
2. Убедитесь что все ENV переменные установлены
3. Проверьте что `DATABASE_URL` и `REDIS_URL` правильные

### 3. WebSocket не работает

**Проблема**: Real-time обновления не приходят

**Решение**:
1. Убедитесь что используется `daphne` (не gunicorn)
2. Проверьте что `REDIS_URL` правильный
3. Проверьте в логах: `Connected to Redis` должно быть

### 4. Static files не загружаются

**Проблема**: CSS/JS не работают

**Решение**:
1. Запустите вручную:
   ```bash
   python manage.py collectstatic --no-input
   ```
2. Убедитесь что `STATIC_ROOT` настроен правильно
3. Проверьте что `whitenoise` в `MIDDLEWARE`

### 5. Database connection error

**Проблема**: `Could not connect to database`

**Решение**:
1. Проверьте что PostgreSQL сервис запущен (зеленый статус)
2. Проверьте `DATABASE_URL` в ENV переменных
3. Убедитесь что используете **Internal URL**, не External

### 6. Redis connection error

**Проблема**: `Error connecting to Redis`

**Решение**:
1. Проверьте что Redis сервис запущен
2. Проверьте `REDIS_URL` формат: `redis://host:6379`
3. Используйте **Internal Redis URL**

## Важные замечания ⚠️

### Free Plan ограничения:
- **Web Service**: спит после 15 минут неактивности (первый запрос будет медленным)
- **PostgreSQL**: 1GB storage, 90 дней истории
- **Redis**: 25MB memory

### Рекомендации:
1. **Смените пароль админа** сразу после деплоя
2. **Настройте Sentry** для отслеживания ошибок в production
3. **Backup БД** регулярно (Render делает автоматически, но лучше иметь свой)
4. **Мониторьте логи** первые дни после деплоя

## Обновление приложения

После внесения изменений в код:

```bash
git add .
git commit -m "feat: Your changes"
git push origin main
```

Render автоматически:
1. Обнаружит изменения в GitHub
2. Запустит новый build
3. Выполнит миграции
4. Перезапустит сервис

**Время деплоя**: обычно 3-5 минут

## Полезные ссылки

- 📚 Render Docs: https://render.com/docs
- 🐍 Django on Render: https://render.com/docs/deploy-django
- 🔌 WebSocket on Render: https://render.com/docs/websockets
- 💾 PostgreSQL: https://render.com/docs/databases
- 🔴 Redis: https://render.com/docs/redis

## Поддержка

Если что-то не работает:
1. Проверьте логи в Render Dashboard
2. Проверьте что все ENV переменные установлены
3. Попробуйте Manual Deploy
4. Обратитесь в Render Support (очень отзывчивые!)

---

**Готово!** 🎉 Ваша ERP система теперь доступна в интернете 24/7!

URL: `https://erp-system.onrender.com` (или ваш кастомный домен)

