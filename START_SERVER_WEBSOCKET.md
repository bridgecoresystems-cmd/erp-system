# Запуск сервера с WebSocket

## ⚠️ Важно!

Для работы WebSocket нужно использовать **Daphne** вместо обычного `runserver`.

## 🚀 Как запустить

### Вариант 1: Daphne (рекомендуется для WebSocket)

```bash
cd /home/batyr/projects/erp-system/factory_erp
../venv/bin/daphne -b 0.0.0.0 -p 8000 factory_erp.asgi:application
```

### Вариант 2: Обычный runserver (только для разработки без WebSocket)

```bash
cd /home/batyr/projects/erp-system/factory_erp
../venv/bin/python manage.py runserver 0.0.0.0:8000
```

**Примечание:** В Django 5.x обычный `runserver` также может работать с WebSocket через Daphne автоматически.

## ✅ Проверка WebSocket

После запуска откройте:
```
http://localhost:8000/lohia/dashboard/
```

В консоли браузера (F12) должно быть:
```
🚀 Инициализация Lohia dashboard с WebSocket
🔌 Подключение к WebSocket: ws://localhost:8000/ws/lohia/dashboard/
✅ WebSocket подключен к Lohia dashboard
```

На странице вверху должно быть:
```
🟢 WebSocket подключен
```

## 🔧 Если WebSocket не подключается

### 1. Проверьте, что Daphne установлен:

```bash
cd /home/batyr/projects/erp-system
source venv/bin/activate
pip list | grep -i daphne
```

Должно быть: `daphne`

### 2. Проверьте channels и channels_redis:

```bash
pip list | grep -i channels
```

Должно быть:
- `channels`
- `channels-redis`

### 3. Если не установлено, установите:

```bash
pip install daphne channels channels-redis
```

### 4. Проверьте Redis:

WebSocket использует Redis для channel layer. Проверьте что Redis запущен:

```bash
redis-cli ping
```

Должно ответить: `PONG`

Если Redis не запущен:

```bash
sudo systemctl start redis
# или
sudo service redis start
```

## 📋 URL WebSocket

Dashboard использует WebSocket по адресу:
```
ws://localhost:8000/ws/lohia/dashboard/
```

Этот URL определен в:
- `factory_erp/factory_erp/routing.py` - маршруты WebSocket
- `factory_erp/factory_erp/consumers.py` - LohiaConsumer обрабатывает подключения

## 🔄 Как работает

1. **Страница загружается** → Dashboard.html
2. **JavaScript подключается** → `ws://localhost:8000/ws/lohia/dashboard/`
3. **Consumer отправляет данные** → LohiaConsumer.get_machines()
4. **Браузер получает данные** → Обновляется таблица
5. **При изменениях** → Данные обновляются автоматически через WebSocket

## 🎯 Преимущества WebSocket

- ✅ Мгновенное обновление данных
- ✅ Нет задержек как в AJAX polling
- ✅ Меньше нагрузки на сервер
- ✅ Двусторонняя связь
- ✅ Единая система как в других частях проекта

---

**После запуска сервера откройте:**
```
http://localhost:8000/lohia/dashboard/
```

