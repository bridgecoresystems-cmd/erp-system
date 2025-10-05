#!/bin/bash

echo "🔧 Создание базы данных PostgreSQL для ERP системы..."

# Создаем пользователя
echo "Создаем пользователя erp_user..."
sudo -u postgres psql -c "CREATE USER erp_user WITH PASSWORD 'erp_password123';" 2>/dev/null || echo "Пользователь уже существует"

# Создаем базу данных
echo "Создаем базу данных factory_erp_db..."
sudo -u postgres psql -c "CREATE DATABASE factory_erp_db OWNER erp_user;" 2>/dev/null || echo "База данных уже существует"

# Предоставляем привилегии
echo "Предоставляем привилегии..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE factory_erp_db TO erp_user;" 2>/dev/null || echo "Привилегии уже предоставлены"

# Настраиваем привилегии в базе данных
echo "Настраиваем привилегии в базе данных..."
sudo -u postgres psql -d factory_erp_db -c "GRANT ALL ON SCHEMA public TO erp_user;" 2>/dev/null || echo "Привилегии схемы уже настроены"
sudo -u postgres psql -d factory_erp_db -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO erp_user;" 2>/dev/null || echo "Привилегии по умолчанию уже настроены"

echo "✅ База данных настроена!"
echo "📋 Параметры подключения:"
echo "   База данных: factory_erp_db"
echo "   Пользователь: erp_user"
echo "   Пароль: erp_password123"
echo "   Хост: localhost"
echo "   Порт: 5432"

echo ""
echo "🔍 Проверяем подключение..."
PGPASSWORD=erp_password123 psql -h localhost -U erp_user -d factory_erp_db -c "SELECT current_database(), current_user;" 2>/dev/null && echo "✅ Подключение успешно!" || echo "❌ Ошибка подключения"
