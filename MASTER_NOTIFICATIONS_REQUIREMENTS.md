# 📱 Master Notifications - Required Extensions

## 🔔 **Для уведомлений мастеру на телефон нужно скачать:**

### **1. 📧 Email уведомления (обязательно):**
```bash
# Основные пакеты для email
django-email-backends
django-smtp-ssl
```

### **2. 📱 SMS уведомления (опционально):**
```bash
# SMS через различные провайдеры
django-sms
twilio
```

### **3. 🔔 Push уведомления (опционально):**
```bash
# Push уведомления
django-push-notifications
pyfcm
```

### **4. 📲 Telegram Bot (рекомендуется):**
```bash
# Telegram Bot API
python-telegram-bot
requests
```

### **5. 📞 WhatsApp (опционально):**
```bash
# WhatsApp Business API
whatsapp-web
selenium
```

## 🎯 **Рекомендуемый минимальный набор:**

### **Для начала (Email + Telegram):**
1. **django-email-backends** - для email
2. **python-telegram-bot** - для Telegram
3. **requests** - для HTTP запросов

### **Команды для скачивания:**
```bash
# Email
pip download --no-index --find-links https://pypi.org/simple/ django-email-backends --dest ~/projects/requirements/

# Telegram
pip download --no-index --find-links https://pypi.org/simple/ python-telegram-bot --dest ~/projects/requirements/
pip download --no-index --find-links https://pypi.org/simple/ requests --dest ~/projects/requirements/
```

## 🚀 **План реализации:**

### **1. Создать модель Master:**
```python
class Master(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    telegram_chat_id = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
```

### **2. Создать модель MaintenanceCall:**
```python
class MaintenanceCall(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(User, on_delete=models.CASCADE)
    master = models.ForeignKey(Master, on_delete=models.CASCADE)
    call_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершен')
    ])
    description = models.TextField(blank=True)
```

### **3. Создать страницу для мастера:**
- Кнопка "Вызвать мастера"
- Выбор мастера из списка
- Описание проблемы
- Отправка уведомлений

### **4. WebSocket для реального времени:**
- Уведомления о новых вызовах
- Обновление статуса вызовов
- Чат с мастером

## 📋 **Следующие шаги:**

1. **Скачать расширения** (Email + Telegram)
2. **Создать модели** Master и MaintenanceCall
3. **Настроить Telegram Bot**
4. **Создать страницу вызова мастера**
5. **Добавить WebSocket уведомления**

---

**🎯 Готов начать с Email + Telegram уведомлений?**
