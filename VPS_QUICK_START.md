# ⚡ Quick Start - Деплой на VPS за 30 минут

## ✅ Чеклист быстрого деплоя

### 1. Подключение к VPS (2 минуты)
```bash
ssh root@148.230.81.243
adduser deploy
usermod -aG sudo deploy
su - deploy
```

### 2. Установка пакетов (5 минут)
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx supervisor redis-server postgresql postgresql-contrib libpq-dev ufw
```

### 3. PostgreSQL (3 минуты)
```bash
sudo -u postgres psql
```
```sql
CREATE USER erp_user WITH PASSWORD 'ТВОЙ_ПАРОЛЬ';
CREATE DATABASE factory_erp_db OWNER erp_user;
GRANT ALL PRIVILEGES ON DATABASE factory_erp_db TO erp_user;
\q
```

### 4. Клонирование проекта (2 минуты)
```bash
cd ~
git clone https://github.com/bridgecoresystems-cmd/erp-system.git
cd erp-system
git checkout websocket-postgres
```

### 5. Virtual Environment (3 минуты)
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Settings Production (3 минуты)
```bash
cd factory_erp/factory_erp
cp settings.py settings_production.py
nano settings_production.py
```
Измени:
- `DEBUG = False`
- `ALLOWED_HOSTS = ['YOUR_IP']`
- `DATABASES` password
- `SECRET_KEY`

### 7. Миграции и статика (3 минуты)
```bash
cd ~/erp-system/factory_erp
python manage.py migrate --settings=factory_erp.settings_production
python manage.py createsuperuser --settings=factory_erp.settings_production
python manage.py collectstatic --noinput --settings=factory_erp.settings_production
```

### 8. Supervisor (3 минуты)
```bash
sudo nano /etc/supervisor/conf.d/daphne.conf
```
Скопируй из `VPS_DEPLOYMENT_GUIDE.md` секцию Supervisor

```bash
sudo mkdir -p /run/daphne
sudo chown deploy:deploy /run/daphne
mkdir -p ~/erp-system/logs
sudo supervisorctl reread && sudo supervisorctl update
sudo supervisorctl status
```

### 9. Nginx (3 минуты)
```bash
sudo nano /etc/nginx/sites-available/erp-system
```
Скопируй из `VPS_DEPLOYMENT_GUIDE.md` секцию Nginx
(уже настроено: erp.bridgecore.tech и 148.230.81.243)

```bash
sudo ln -s /etc/nginx/sites-available/erp-system /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 10. Firewall (1 минута)
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 11. Проверка (2 минуты)
```bash
sudo supervisorctl status
# Открой в браузере: http://148.230.81.243 или https://erp.bridgecore.tech
```

---

## 🎉 Готово за 30 минут!

**Следующие шаги:**
1. ✅ Домен настроен: erp.bridgecore.tech
2. Установи SSL: `sudo certbot --nginx -d erp.bridgecore.tech -d www.erp.bridgecore.tech`
3. Обнови `settings_production.py`: `SECURE_SSL_REDIRECT = True`

---

## 🔥 Быстрые команды

### Перезапуск всех сервисов:
```bash
sudo supervisorctl restart all
sudo systemctl restart nginx
```

### Проверка логов:
```bash
tail -f ~/erp-system/logs/daphne.log
tail -f ~/erp-system/logs/celery.log
sudo tail -f /var/log/nginx/error.log
```

### Обновление кода:
```bash
cd ~/erp-system
git pull origin websocket-postgres
source venv/bin/activate
pip install -r requirements.txt
cd factory_erp
python manage.py migrate --settings=factory_erp.settings_production
python manage.py collectstatic --noinput --settings=factory_erp.settings_production
sudo supervisorctl restart all
```

---

## 📞 Проблемы?

Смотри полный гайд: `VPS_DEPLOYMENT_GUIDE.md`

