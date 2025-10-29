# 🚀 Руководство по деплою на PythonAnywhere

## 📋 Содержание
1. [Подготовка](#подготовка)
2. [Регистрация на PythonAnywhere](#регистрация)
3. [Загрузка проекта](#загрузка-проекта)
4. [Настройка окружения](#настройка-окружения)
5. [Конфигурация Web App](#конфигурация-web-app)
6. [Миграции и статика](#миграции-и-статика)
7. [Проверка и тестирование](#проверка)
8. [Решение проблем](#решение-проблем)

---

## 1. Подготовка

### Что уже готово:
✅ SQLite база данных  
✅ AJAX polling вместо WebSocket  
✅ Все зависимости обновлены  
✅ Production настройки созданы  
✅ WSGI конфигурация готова  

### Файлы конфигурации:
- `pythonanywhere_wsgi.py` - WSGI application
- `factory_erp/factory_erp/settings_pythonanywhere.py` - Production settings
- `requirements.txt` - Python зависимости

---

## 2. Регистрация на PythonAnywhere

1. Перейдите на [https://www.pythonanywhere.com](https://www.pythonanywhere.com)
2. Нажмите "Start running Python online in less than a minute"
3. Создайте **бесплатный** аккаунт (Beginner)
4. Подтвердите email

**Бесплатный план включает:**
- 512 MB дискового пространства
- 1 Web App
- SQLite база данных
- HTTP (не HTTPS на бесплатном плане)
- Домен: `yourusername.pythonanywhere.com`

---

## 3. Загрузка проекта

### Вариант A: Через Git (рекомендуется)

1. Откройте **Consoles → Bash**

2. Клонируйте репозиторий:
```bash
cd ~
git clone https://github.com/yourusername/erp-system.git
cd erp-system
```

3. Переключитесь на `main` ветку (AJAX версия):
```bash
git checkout main
```

### Вариант B: Через файловый менеджер

1. Откройте **Files**
2. Создайте папку `erp-system`
3. Загрузите файлы через Upload
   ⚠️ **Внимание:** Не загружайте папки `venv/`, `__pycache__/`, `*.pyc`

---

## 4. Настройка окружения

### 4.1 Создание виртуального окружения

В Bash консоли:
```bash
cd ~/erp-system
mkvirtualenv --python=/usr/bin/python3.10 erp-venv
```

### 4.2 Установка зависимостей

```bash
workon erp-venv
pip install -r requirements.txt
```

**Примечание:** Установка может занять 5-10 минут

### 4.3 Проверка установки

```bash
python -c "import django; print(django.get_version())"
# Должно вывести версию Django (например: 4.2.x)
```

---

## 5. Конфигурация Web App

### 5.1 Создание Web App

1. Перейдите в **Web → Add a new web app**
2. Выберите:
   - **Framework:** Manual configuration
   - **Python version:** Python 3.10
3. Нажмите **Next**

### 5.2 Настройка WSGI файла

1. В разделе **Code** найдите "WSGI configuration file"
2. Кликните на ссылку файла (например: `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
3. **Удалите** всё содержимое файла
4. Скопируйте содержимое из `/home/yourusername/erp-system/pythonanywhere_wsgi.py`
5. **ВАЖНО:** Замените `yourusername` на ваше имя пользователя PythonAnywhere
6. Сохраните (Ctrl+S или кнопка Save)

**Пример после замены:**
```python
path = '/home/batyr/erp-system/factory_erp'  # ← ваше имя
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'factory_erp.settings_pythonanywhere'
```

### 5.3 Настройка Virtual Environment

1. В разделе **Virtualenv**
2. Введите путь к виртуальному окружению:
```
/home/yourusername/.virtualenvs/erp-venv
```
3. Замените `yourusername` на ваше имя
4. Нажмите ✓ (галочка)

### 5.4 Настройка Source code

В разделе **Code:**
- **Source code:** `/home/yourusername/erp-system/factory_erp`

### 5.5 Настройка Static files

В разделе **Static files** добавьте 2 записи:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/erp-system/factory_erp/staticfiles` |
| `/media/` | `/home/yourusername/erp-system/factory_erp/media` |

Замените `yourusername` на ваше имя!

---

## 6. Миграции и статика

### 6.1 Обновление settings_pythonanywhere.py

Откройте Bash консоль и отредактируйте:
```bash
cd ~/erp-system/factory_erp/factory_erp
nano settings_pythonanywhere.py
```

Замените:
```python
ALLOWED_HOSTS = [
    'yourusername.pythonanywhere.com',  # ← Ваше имя!
    '127.0.0.1',
    'localhost',
]

SECRET_KEY = 'СГЕНЕРИРУЙТЕ_НОВЫЙ_КЛЮЧ'  # См. ниже
```

**Генерация SECRET_KEY:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```
Скопируйте вывод и вставьте в `SECRET_KEY`

Сохраните: Ctrl+X → Y → Enter

### 6.2 Применение миграций

```bash
cd ~/erp-system/factory_erp
workon erp-venv

# Применяем миграции
python manage.py migrate --settings=factory_erp.settings_pythonanywhere

# Создаем суперпользователя
python manage.py createsuperuser --settings=factory_erp.settings_pythonanywhere
# Введите: username, email (можно пропустить), password

# Собираем статические файлы
python manage.py collectstatic --noinput --settings=factory_erp.settings_pythonanywhere
```

**Примечание:** Команды должны завершиться без ошибок

### 6.3 Создание тестовых данных (опционально)

```bash
# Если у вас есть фикстуры:
python manage.py loaddata fixtures/employees.json --settings=factory_erp.settings_pythonanywhere

# Или создайте данные через Django shell:
python manage.py shell --settings=factory_erp.settings_pythonanywhere
```

---

## 7. Проверка и тестирование

### 7.1 Reload Web App

1. Вернитесь на страницу **Web**
2. Нажмите большую зеленую кнопку **"Reload yourusername.pythonanywhere.com"**
3. Подождите 10-15 секунд

### 7.2 Проверка сайта

Откройте в браузере: `https://yourusername.pythonanywhere.com`

✅ **Должно работать:**
- Страница загружается
- Статика (CSS, JS, изображения) подгружается
- Можно войти в админку: `/admin/`
- AJAX polling обновляет данные каждые 5 секунд

⚠️ **Известные ограничения бесплатного плана:**
- HTTP only (не HTTPS)
- Сайт "засыпает" после 3 месяцев неактивности
- Нужно заходить в Web раз в 3 месяца и нажимать "Reload"

### 7.3 Тестирование функциональности

1. **Админка:** `https://yourusername.pythonanywhere.com/admin/`
   - Войдите под суперпользователем
   - Создайте тестовых сотрудников

2. **Сотрудники:** `/employees/`
   - Проверьте отображение списка
   - AJAX должен работать (обновление каждые 5 сек)

3. **Lohia мониторинг:** `/lohia/dashboard/`
   - Проверьте дашборд станков

4. **ESP32 API:** Протестируйте с ESP32 или через curl:
```bash
curl -X POST https://yourusername.pythonanywhere.com/employees/api/rfid-scan/ \
  -H "Content-Type: application/json" \
  -d '{"device_id": "DEVICE001", "rfid_uid": "test123"}'
```

---

## 8. Решение проблем

### 🔴 Ошибка 500 - Internal Server Error

**Причина:** Ошибка в коде или настройках

**Решение:**
1. Откройте **Web → Log files → Error log**
2. Посмотрите последние строки
3. Исправьте ошибку
4. Нажмите **Reload**

**Частые причины:**
- Неправильный путь в WSGI файле
- SECRET_KEY не заменен
- ALLOWED_HOSTS не содержит ваш домен
- Миграции не применены

### 🔴 Статика не загружается

**Причина:** Неправильно настроены Static files

**Решение:**
1. Проверьте пути в **Web → Static files**
2. Убедитесь что файлы существуют:
```bash
ls ~/erp-system/factory_erp/staticfiles/
```
3. Пересоберите статику:
```bash
cd ~/erp-system/factory_erp
workon erp-venv
python manage.py collectstatic --clear --noinput --settings=factory_erp.settings_pythonanywhere
```
4. Reload Web App

### 🔴 База данных не найдена

**Причина:** SQLite файл не создан или неправильный путь

**Решение:**
```bash
cd ~/erp-system/factory_erp
workon erp-venv
python manage.py migrate --settings=factory_erp.settings_pythonanywhere
```

Проверьте что файл создан:
```bash
ls -lh ~/erp-system/factory_erp/db.sqlite3
```

### 🔴 ModuleNotFoundError

**Причина:** Не установлены зависимости

**Решение:**
```bash
workon erp-venv
pip install -r ~/erp-system/requirements.txt
```

Reload Web App

### 🟡 AJAX не обновляет данные

**Причина:** JavaScript ошибки или API недоступен

**Решение:**
1. Откройте Developer Tools (F12) → Console
2. Проверьте ошибки JavaScript
3. Проверьте Network tab - запросы к API должны возвращать 200 OK
4. Убедитесь что URL API правильные

---

## 📝 Обновление сайта

После изменений в коде:

```bash
cd ~/erp-system
git pull origin main
workon erp-venv
pip install -r requirements.txt  # Если зависимости изменились
cd factory_erp
python manage.py migrate --settings=factory_erp.settings_pythonanywhere  # Если есть новые миграции
python manage.py collectstatic --noinput --settings=factory_erp.settings_pythonanywhere  # Если изменилась статика
```

Затем: **Web → Reload**

---

## 🔐 Безопасность

### Для production (платный план с HTTPS):

В `settings_pythonanywhere.py` включите:
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### Для бесплатного плана:

⚠️ Не храните чувствительные данные!  
⚠️ Используйте только для демо/тестирования  

---

## 📊 Мониторинг

### Логи

**Error log:** `Web → Log files → Error log`  
**Server log:** `Web → Log files → Server log`  
**Access log:** `Web → Log files → Access log`

### Использование ресурсов

**Files:** Проверьте использование диска (лимит 512 MB)  
**CPU:** На бесплатном плане лимит 100 секунд/день

---

## 🎉 Готово!

Ваш ERP система теперь доступна по адресу:
```
https://yourusername.pythonanywhere.com
```

### Что работает:
✅ Управление сотрудниками  
✅ Учет рабочего времени  
✅ Lohia мониторинг станков  
✅ Security access control  
✅ ESP32 API endpoints  
✅ AJAX polling (обновление каждые 5 сек)  
✅ Админка Django  

### Для перехода на VPS в будущем:
```bash
git checkout websocket-postgres
# Настроить PostgreSQL + Redis
# Деплой с полной WebSocket поддержкой
```

---

## 📞 Поддержка

**PythonAnywhere форумы:** https://www.pythonanywhere.com/forums/  
**Документация:** https://help.pythonanywhere.com/  

**Проблемы с проектом:**
Создайте issue на GitHub или проверьте `AJAX_MIGRATION_GUIDE.md`

