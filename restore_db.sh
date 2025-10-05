#!/bin/bash

# Скрипт для восстановления базы данных PostgreSQL из резервной копии
# ERP система - Factory ERP

# Настройки
DB_NAME="factory_erp_db"
DB_USER="erp_user"
DB_PASSWORD="erp_password123"
BACKUP_DIR="/home/batyr/projects/erp-system/backups"
LOG_FILE="${BACKUP_DIR}/restore.log"

# Функция логирования
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Функция показа справки
show_help() {
    echo "Использование: $0 [OPTIONS]"
    echo ""
    echo "Опции:"
    echo "  -f FILE    Путь к файлу резервной копии"
    echo "  -l         Показать список доступных резервных копий"
    echo "  -h         Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 -f /home/batyr/projects/erp-system/backups/factory_erp_backup_20251005_131500.sql.gz"
    echo "  $0 -l"
    echo ""
}

# Функция показа списка бэкапов
show_backups() {
    echo "📋 Доступные резервные копии:"
    echo ""
    if [ -d "$BACKUP_DIR" ]; then
        ls -lh "${BACKUP_DIR}"/factory_erp_backup_*.sql.gz 2>/dev/null | while read line; do
            echo "   $line"
        done
    else
        echo "   Директория с резервными копиями не найдена: $BACKUP_DIR"
    fi
    echo ""
}

# Парсинг аргументов
BACKUP_FILE=""
while getopts "f:lh" opt; do
    case $opt in
        f) BACKUP_FILE="$OPTARG" ;;
        l) show_backups; exit 0 ;;
        h) show_help; exit 0 ;;
        *) show_help; exit 1 ;;
    esac
done

# Проверяем, что указан файл
if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Ошибка: Не указан файл резервной копии"
    echo ""
    show_help
    exit 1
fi

# Проверяем существование файла
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Ошибка: Файл '$BACKUP_FILE' не найден"
    echo ""
    show_backups
    exit 1
fi

# Начинаем восстановление
log_message "🔄 Начинаем восстановление базы данных $DB_NAME из файла: $BACKUP_FILE"

# Проверяем подключение к PostgreSQL
if ! PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
    log_message "❌ Ошибка: Не удается подключиться к PostgreSQL"
    exit 1
fi

# Создаем резервную копию текущего состояния (на всякий случай)
CURRENT_BACKUP="${BACKUP_DIR}/factory_erp_current_before_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
log_message "💾 Создаем резервную копию текущего состояния: $CURRENT_BACKUP"

if PGPASSWORD="$DB_PASSWORD" pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" \
    --verbose --clean --no-owner --no-privileges | gzip > "$CURRENT_BACKUP"; then
    log_message "✅ Резервная копия текущего состояния создана"
else
    log_message "⚠️ Предупреждение: Не удалось создать резервную копию текущего состояния"
fi

# Останавливаем Django сервер (если запущен)
if pgrep -f "python3 manage.py runserver" > /dev/null; then
    log_message "🛑 Останавливаем Django сервер..."
    pkill -f "python3 manage.py runserver"
    sleep 2
fi

# Удаляем и пересоздаем базу данных
log_message "🗑️ Удаляем текущую базу данных..."
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

log_message "🆕 Создаем новую базу данных..."
PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Восстанавливаем данные
log_message "📥 Восстанавливаем данные из резервной копии..."

if [[ "$BACKUP_FILE" == *.gz ]]; then
    # Сжатый файл
    if gunzip -c "$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d "$DB_NAME"; then
        log_message "✅ Восстановление завершено успешно!"
    else
        log_message "❌ Ошибка при восстановлении данных!"
        exit 1
    fi
else
    # Обычный файл
    if PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_FILE"; then
        log_message "✅ Восстановление завершено успешно!"
    else
        log_message "❌ Ошибка при восстановлении данных!"
        exit 1
    fi
fi

# Проверяем восстановление
log_message "🔍 Проверяем восстановленную базу данных..."
TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
log_message "📊 Количество таблиц: $TABLE_COUNT"

USER_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM auth_user;" 2>/dev/null | xargs || echo "0")
log_message "👥 Количество пользователей: $USER_COUNT"

log_message "🎉 Восстановление базы данных завершено!"
echo ""
echo "📋 Сводка восстановления:"
echo "   База данных: $DB_NAME"
echo "   Источник: $BACKUP_FILE"
echo "   Таблиц: $TABLE_COUNT"
echo "   Пользователей: $USER_COUNT"
echo "   Время: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "💡 Теперь можете запустить Django сервер:"
echo "   cd /home/batyr/projects/erp-system/factory_erp"
echo "   source ../venv/bin/activate"
echo "   python3 manage.py runserver"
echo ""
