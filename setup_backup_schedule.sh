#!/bin/bash

# Скрипт для настройки автоматического резервного копирования
# ERP система - Factory ERP

BACKUP_SCRIPT="/home/batyr/projects/erp-system/backup_db.sh"
CRON_JOB_FILE="/tmp/erp_backup_cron"

echo "🔧 Настройка автоматического резервного копирования..."

# Проверяем существование скрипта бэкапа
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "❌ Ошибка: Скрипт бэкапа не найден: $BACKUP_SCRIPT"
    exit 1
fi

# Создаем cron задачу
echo "📅 Создаем расписание резервного копирования..."

# Варианты расписания
echo "Выберите расписание для автоматического резервного копирования:"
echo ""
echo "1. Каждый день в 02:00 (рекомендуется)"
echo "2. Каждый день в 03:00"
echo "3. Каждые 6 часов"
echo "4. Каждые 12 часов"
echo "5. Только по выходным в 02:00"
echo "6. Пользовательский вариант"
echo "7. Отключить автоматическое резервное копирование"
echo ""

read -p "Введите номер (1-7): " choice

case $choice in
    1)
        CRON_SCHEDULE="0 2 * * *"
        DESCRIPTION="каждый день в 02:00"
        ;;
    2)
        CRON_SCHEDULE="0 3 * * *"
        DESCRIPTION="каждый день в 03:00"
        ;;
    3)
        CRON_SCHEDULE="0 */6 * * *"
        DESCRIPTION="каждые 6 часов"
        ;;
    4)
        CRON_SCHEDULE="0 */12 * * *"
        DESCRIPTION="каждые 12 часов"
        ;;
    5)
        CRON_SCHEDULE="0 2 * * 0"
        DESCRIPTION="каждое воскресенье в 02:00"
        ;;
    6)
        echo ""
        echo "Формат cron: минута час день месяц день_недели"
        echo "Примеры:"
        echo "  0 2 * * *     - каждый день в 02:00"
        echo "  0 */6 * * *   - каждые 6 часов"
        echo "  30 1 * * 1    - каждый понедельник в 01:30"
        echo ""
        read -p "Введите расписание cron: " CRON_SCHEDULE
        DESCRIPTION="пользовательское расписание: $CRON_SCHEDULE"
        ;;
    7)
        echo "🗑️ Отключаем автоматическое резервное копирование..."
        
        # Удаляем существующие cron задачи
        (crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT") | crontab -
        
        echo "✅ Автоматическое резервное копирование отключено"
        echo ""
        echo "💡 Для ручного резервного копирования используйте:"
        echo "   $BACKUP_SCRIPT"
        exit 0
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac

# Создаем cron задачу
echo "📝 Настраиваем cron задачу: $DESCRIPTION"

# Получаем текущие cron задачи (исключая наш скрипт)
(crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT"; echo "$CRON_SCHEDULE $BACKUP_SCRIPT >> /home/batyr/projects/erp-system/backups/cron.log 2>&1") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Автоматическое резервное копирование настроено!"
    echo ""
    echo "📋 Настройки:"
    echo "   Расписание: $DESCRIPTION"
    echo "   Скрипт: $BACKUP_SCRIPT"
    echo "   Лог: /home/batyr/projects/erp-system/backups/cron.log"
    echo ""
    echo "📅 Текущие cron задачи:"
    crontab -l | grep -E "(backup|erp)" || echo "   (задачи не найдены)"
    echo ""
    echo "💡 Полезные команды:"
    echo "   crontab -l                    - показать все cron задачи"
    echo "   crontab -e                    - редактировать cron задачи"
    echo "   tail -f /home/batyr/projects/erp-system/backups/cron.log - просмотр логов"
    echo "   $BACKUP_SCRIPT               - ручной бэкап"
    echo ""
    echo "🔍 Для проверки работы:"
    echo "   sudo systemctl status cron    - статус cron сервиса"
    echo "   sudo systemctl start cron     - запустить cron сервис"
    echo "   sudo systemctl enable cron    - включить автозапуск cron"
else
    echo "❌ Ошибка при настройке cron задачи"
    exit 1
fi
