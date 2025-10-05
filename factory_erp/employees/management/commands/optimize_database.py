# employees/management/commands/optimize_database.py
from django.core.management.base import BaseCommand
from django.db import connection
from employees.models import Employee, CardAccess, WorkTimeEntry

class Command(BaseCommand):
    help = 'Оптимизация базы данных ERP системы'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем оптимизацию базы данных...')
        
        # Создаем индексы для улучшения производительности
        with connection.cursor() as cursor:
            # Индексы для Employee
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_employee_rfid ON employees_employee(rfid_uid);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_employee_active ON employees_employee(is_active);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_employee_department ON employees_employee(department);")
                self.stdout.write('✓ Индексы для Employee созданы')
            except Exception as e:
                self.stdout.write(f'⚠ Ошибка создания индексов Employee: {e}')
            
            # Индексы для CardAccess
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cardaccess_timestamp ON employees_cardaccess(timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cardaccess_success ON employees_cardaccess(success);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cardaccess_employee ON employees_cardaccess(employee_id);")
                self.stdout.write('✓ Индексы для CardAccess созданы')
            except Exception as e:
                self.stdout.write(f'⚠ Ошибка создания индексов CardAccess: {e}')
            
            # Индексы для WorkTimeEntry
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_worktime_date ON employees_worktimeentry(date);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_worktime_employee ON employees_worktimeentry(employee_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_worktime_status ON employees_worktimeentry(status);")
                self.stdout.write('✓ Индексы для WorkTimeEntry созданы')
            except Exception as e:
                self.stdout.write(f'⚠ Ошибка создания индексов WorkTimeEntry: {e}')
        
        # Очистка старых записей (старше 1 года)
        try:
            from datetime import date, timedelta
            one_year_ago = date.today() - timedelta(days=365)
            
            old_accesses = CardAccess.objects.filter(timestamp__date__lt=one_year_ago)
            count = old_accesses.count()
            if count > 0:
                old_accesses.delete()
                self.stdout.write(f'✓ Удалено {count} старых записей доступа')
            else:
                self.stdout.write('✓ Старых записей доступа не найдено')
        except Exception as e:
            self.stdout.write(f'⚠ Ошибка очистки старых записей: {e}')
        
        # Статистика базы данных
        try:
            employee_count = Employee.objects.filter(is_active=True).count()
            access_count = CardAccess.objects.count()
            worktime_count = WorkTimeEntry.objects.count()
            
            self.stdout.write('\n📊 Статистика базы данных:')
            self.stdout.write(f'  • Активных сотрудников: {employee_count}')
            self.stdout.write(f'  • Записей доступа: {access_count}')
            self.stdout.write(f'  • Записей рабочего времени: {worktime_count}')
        except Exception as e:
            self.stdout.write(f'⚠ Ошибка получения статистики: {e}')
        
        self.stdout.write('\n✅ Оптимизация базы данных завершена!')
