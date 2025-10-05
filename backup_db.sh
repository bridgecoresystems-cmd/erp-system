#!/bin/bash

# Скрипт для резервного копирования базы данных PostgreSQL
# ERP система - Factory ERP

# Настройки
DB_NAME="factory_erp_db"
DB_USER="erp_user"
DB_PASSWORD="erp_password123"
BACKUP_DIR="/home/batyr/projects/erp-system/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/factory_erp_backup_${DATE}.sql"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Создаем директорию для бэкапов, если не существует
mkdir -p "$BACKUP_DIR"

# Функция логирования
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Начинаем резервное копирование
log_message "🔄 Начинаем резервное копирование базы данных $DB_NAME..."

# Проверяем подключение к базе данных
if ! PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    log_message "❌ Ошибка: Не удается подключиться к базе данных $DB_NAME"
    exit 1
fi

# Создаем резервную копию
log_message "📦 Создаем резервную копию в файл: $BACKUP_FILE"

if PGPASSWORD="$DB_PASSWORD" pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" \
    --verbose --clean --no-owner --no-privileges \
    --format=plain --file="$BACKUP_FILE"; then
    
    # Проверяем размер файла
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_message "✅ Резервное копирование завершено успешно!"
    log_message "📊 Размер файла: $BACKUP_SIZE"
    log_message "📍 Путь к файлу: $BACKUP_FILE"
    
    # Создаем сжатую версию
    COMPRESSED_FILE="${BACKUP_FILE}.gz"
    if gzip -c "$BACKUP_FILE" > "$COMPRESSED_FILE"; then
        COMPRESSED_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
        log_message "🗜️ Сжатая версия: $COMPRESSED_FILE ($COMPRESSED_SIZE)"
        rm "$BACKUP_FILE"  # Удаляем несжатую версию
        log_message "🗑️ Удален несжатый файл для экономии места"
    fi
    
    # Очищаем старые бэкапы (оставляем последние 10)
    OLD_BACKUPS=$(ls -t "${BACKUP_DIR}"/factory_erp_backup_*.sql.gz 2>/dev/null | tail -n +11)
    if [ -n "$OLD_BACKUPS" ]; then
        echo "$OLD_BACKUPS" | xargs rm -f
        log_message "🧹 Удалены старые резервные копии (оставлены последние 10)"
    fi
    
    # Показываем список всех бэкапов
    log_message "📋 Текущие резервные копии:"
    ls -lh "${BACKUP_DIR}"/factory_erp_backup_*.sql.gz 2>/dev/null | while read line; do
        log_message "   $line"
    done
    
else
    log_message "❌ Ошибка при создании резервной копии!"
    exit 1
fi

log_message "🎉 Резервное копирование завершено!"
echo ""
echo "📋 Сводка:"
echo "   База данных: $DB_NAME"
echo "   Файл бэкапа: $COMPRESSED_FILE"
echo "   Размер: $COMPRESSED_SIZE"
echo "   Время: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
