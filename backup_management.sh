#!/bin/bash

# Управление резервными копиями ERP системы
# Factory ERP - PostgreSQL

BACKUP_DIR="/home/batyr/projects/erp-system/backups"
BACKUP_SCRIPT="/home/batyr/projects/erp-system/backup_db.sh"
RESTORE_SCRIPT="/home/batyr/projects/erp-system/restore_db.sh"

# Функция показа меню
show_menu() {
    echo "🔧 Управление резервными копиями ERP системы"
    echo "=============================================="
    echo ""
    echo "1. 📦 Создать резервную копию"
    echo "2. 📋 Показать список резервных копий"
    echo "3. 🔄 Восстановить из резервной копии"
    echo "4. 📅 Настроить автоматическое резервное копирование"
    echo "5. 📊 Показать статистику резервных копий"
    echo "6. 🗑️ Очистить старые резервные копии"
    echo "7. 📝 Показать логи резервного копирования"
    echo "8. ❓ Справка"
    echo "9. 🚪 Выход"
    echo ""
}

# Функция создания резервной копии
create_backup() {
    echo "📦 Создание резервной копии..."
    echo ""
    if [ -f "$BACKUP_SCRIPT" ]; then
        "$BACKUP_SCRIPT"
    else
        echo "❌ Скрипт резервного копирования не найден: $BACKUP_SCRIPT"
    fi
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

# Функция показа списка резервных копий
show_backups() {
    echo "📋 Список резервных копий:"
    echo ""
    if [ -d "$BACKUP_DIR" ]; then
        ls -lh "${BACKUP_DIR}"/factory_erp_backup_*.sql.gz 2>/dev/null | while read line; do
            echo "   $line"
        done
        
        # Показываем общую статистику
        TOTAL_FILES=$(ls "${BACKUP_DIR}"/factory_erp_backup_*.sql.gz 2>/dev/null | wc -l)
        TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" 2>/dev/null | cut -f1)
        
        echo ""
        echo "📊 Статистика:"
        echo "   Всего файлов: $TOTAL_FILES"
        echo "   Общий размер: $TOTAL_SIZE"
    else
        echo "   Директория с резервными копиями не найдена: $BACKUP_DIR"
    fi
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

# Функция восстановления
restore_backup() {
    echo "🔄 Восстановление из резервной копии..."
    echo ""
    
    if [ -f "$RESTORE_SCRIPT" ]; then
        "$RESTORE_SCRIPT" -l
        echo ""
        read -p "Введите полный путь к файлу резервной копии: " backup_file
        
        if [ -n "$backup_file" ] && [ -f "$backup_file" ]; then
            echo ""
            echo "⚠️ ВНИМАНИЕ: Это действие перезапишет текущую базу данных!"
            read -p "Вы уверены? (yes/no): " confirm
            
            if [ "$confirm" = "yes" ]; then
                "$RESTORE_SCRIPT" -f "$backup_file"
            else
                echo "❌ Восстановление отменено"
            fi
        else
            echo "❌ Файл не найден: $backup_file"
        fi
    else
        echo "❌ Скрипт восстановления не найден: $RESTORE_SCRIPT"
    fi
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

# Функция настройки автоматического резервного копирования
setup_auto_backup() {
    echo "📅 Настройка автоматического резервного копирования..."
    echo ""
    
    SCHEDULE_SCRIPT="/home/batyr/projects/erp-system/setup_backup_schedule.sh"
    if [ -f "$SCHEDULE_SCRIPT" ]; then
        "$SCHEDULE_SCRIPT"
    else
        echo "❌ Скрипт настройки расписания не найден: $SCHEDULE_SCRIPT"
    fi
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

# Функция показа статистики
show_stats() {
    echo "📊 Статистика резервных копий:"
    echo ""
    
    if [ -d "$BACKUP_DIR" ]; then
        # Количество файлов
        TOTAL_FILES=$(ls "${BACKUP_DIR}"/factory_erp_backup_*.sql.gz 2>/dev/null | wc -l)
        
        # Общий размер
        TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" 2>/dev/null | cut -f1)
        
        # Последний бэкап
        LAST_BACKUP=$(ls -t "${BACKUP_DIR}"/factory_erp_backup_*.sql.gz 2>/dev/null | head -n 1)
        if [ -n "$LAST_BACKUP" ]; then
            LAST_BACKUP_DATE=$(stat -c %y "$LAST_BACKUP" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
            LAST_BACKUP_SIZE=$(du -h "$LAST_BACKUP" 2>/dev/null | cut -f1)
        else
            LAST_BACKUP_DATE="Не найден"
            LAST_BACKUP_SIZE="N/A"
        fi
        
        # Статус cron
        CRON_STATUS=$(crontab -l 2>/dev/null | grep -c "$BACKUP_SCRIPT")
        
        echo "   📁 Директория: $BACKUP_DIR"
        echo "   📦 Всего файлов: $TOTAL_FILES"
        echo "   💾 Общий размер: $TOTAL_SIZE"
        echo "   🕒 Последний бэкап: $LAST_BACKUP_DATE"
        echo "   📏 Размер последнего: $LAST_BACKUP_SIZE"
        echo "   ⏰ Автоматические бэкапы: $([ $CRON_STATUS -gt 0 ] && echo "Включены ($CRON_STATUS задач)" || echo "Отключены")"
        
        # Показываем размеры всех файлов
        if [ $TOTAL_FILES -gt 0 ]; then
            echo ""
            echo "📋 Детализация по файлам:"
            ls -lh "${BACKUP_DIR}"/factory_erp_backup_*.sql.gz 2>/dev/null | while read line; do
                echo "   $line"
            done
        fi
    else
        echo "   ❌ Директория с резервными копиями не найдена"
    fi
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

# Функция очистки старых резервных копий
cleanup_old_backups() {
    echo "🗑️ Очистка старых резервных копий..."
    echo ""
    
    if [ -d "$BACKUP_DIR" ]; then
        echo "Текущие резервные копии:"
        ls -lh "${BACKUP_DIR}"/factory_erp_backup_*.sql.gz 2>/dev/null | while read line; do
            echo "   $line"
        done
        
        echo ""
        read -p "Сколько последних резервных копий оставить? (по умолчанию 10): " keep_count
        keep_count=${keep_count:-10}
        
        if [[ "$keep_count" =~ ^[0-9]+$ ]] && [ "$keep_count" -gt 0 ]; then
            echo ""
            echo "🗑️ Удаляем старые резервные копии (оставляем последние $keep_count)..."
            
            # Получаем список файлов для удаления
            files_to_delete=$(ls -t "${BACKUP_DIR}"/factory_erp_backup_*.sql.gz 2>/dev/null | tail -n +$((keep_count + 1)))
            
            if [ -n "$files_to_delete" ]; then
                echo "$files_to_delete" | while read file; do
                    if [ -f "$file" ]; then
                        rm -f "$file"
                        echo "   ✅ Удален: $(basename "$file")"
                    fi
                done
                echo ""
                echo "✅ Очистка завершена!"
            else
                echo "   ℹ️ Нет файлов для удаления"
            fi
        else
            echo "❌ Неверное количество файлов"
        fi
    else
        echo "❌ Директория с резервными копиями не найдена"
    fi
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

# Функция показа логов
show_logs() {
    echo "📝 Логи резервного копирования:"
    echo ""
    
    LOG_FILE="${BACKUP_DIR}/backup.log"
    CRON_LOG="${BACKUP_DIR}/cron.log"
    
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Лог резервного копирования ($LOG_FILE):"
        echo "----------------------------------------"
        tail -n 20 "$LOG_FILE"
        echo ""
    else
        echo "❌ Лог резервного копирования не найден: $LOG_FILE"
    fi
    
    if [ -f "$CRON_LOG" ]; then
        echo "⏰ Лог автоматических бэкапов ($CRON_LOG):"
        echo "----------------------------------------"
        tail -n 20 "$CRON_LOG"
    else
        echo "ℹ️ Лог автоматических бэкапов не найден: $CRON_LOG"
    fi
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

# Функция справки
show_help() {
    echo "❓ Справка по управлению резервными копиями"
    echo "=========================================="
    echo ""
    echo "📦 Резервное копирование:"
    echo "   - Создает полную копию базы данных PostgreSQL"
    echo "   - Сжимает файлы для экономии места"
    echo "   - Автоматически удаляет старые копии (оставляет последние 10)"
    echo ""
    echo "🔄 Восстановление:"
    echo "   - Восстанавливает базу данных из резервной копии"
    echo "   - Создает резервную копию текущего состояния перед восстановлением"
    echo "   - Останавливает Django сервер во время восстановления"
    echo ""
    echo "📅 Автоматическое резервное копирование:"
    echo "   - Настраивается через cron"
    echo "   - Поддерживает различные расписания"
    echo "   - Логи сохраняются в отдельный файл"
    echo ""
    echo "💡 Полезные команды:"
    echo "   ./backup_db.sh                    - ручное резервное копирование"
    echo "   ./restore_db.sh -l                - показать список резервных копий"
    echo "   ./restore_db.sh -f <файл>         - восстановить из файла"
    echo "   ./setup_backup_schedule.sh        - настроить автоматические бэкапы"
    echo "   crontab -l                        - показать cron задачи"
    echo ""
    echo "📁 Файлы и директории:"
    echo "   $BACKUP_DIR                       - директория с резервными копиями"
    echo "   $BACKUP_SCRIPT                    - скрипт резервного копирования"
    echo "   $RESTORE_SCRIPT                   - скрипт восстановления"
    echo ""
    read -p "Нажмите Enter для продолжения..."
}

# Основной цикл программы
while true; do
    clear
    show_menu
    read -p "Выберите действие (1-9): " choice
    
    case $choice in
        1) create_backup ;;
        2) show_backups ;;
        3) restore_backup ;;
        4) setup_auto_backup ;;
        5) show_stats ;;
        6) cleanup_old_backups ;;
        7) show_logs ;;
        8) show_help ;;
        9) 
            echo "👋 До свидания!"
            exit 0
            ;;
        *)
            echo "❌ Неверный выбор. Попробуйте снова."
            sleep 2
            ;;
    esac
done
