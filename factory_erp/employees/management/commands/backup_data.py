# employees/management/commands/backup_data.py
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
import os
import json
from datetime import datetime
from employees.models import Employee, CardAccess, WorkTimeEntry

class Command(BaseCommand):
    help = 'Создание резервной копии данных ERP системы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            help='Формат резервной копии (json, xml)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Путь для сохранения резервной копии'
        )

    def handle(self, *args, **options):
        format_type = options['format']
        output_path = options.get('output')
        
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'backup_erp_{timestamp}.{format_type}'
        
        self.stdout.write(f'Создание резервной копии в формате {format_type}...')
        
        try:
            # Получаем все данные
            employees = Employee.objects.all()
            card_accesses = CardAccess.objects.all()
            worktime_entries = WorkTimeEntry.objects.all()
            
            # Создаем резервную копию
            data = {
                'employees': serializers.serialize(format_type, employees),
                'card_accesses': serializers.serialize(format_type, card_accesses),
                'worktime_entries': serializers.serialize(format_type, worktime_entries),
                'backup_info': {
                    'created_at': datetime.now().isoformat(),
                    'total_employees': employees.count(),
                    'total_accesses': card_accesses.count(),
                    'total_worktime': worktime_entries.count()
                }
            }
            
            # Сохраняем файл
            with open(output_path, 'w', encoding='utf-8') as f:
                if format_type == 'json':
                    json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    f.write(data)
            
            # Получаем размер файла
            file_size = os.path.getsize(output_path)
            file_size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(f'✅ Резервная копия создана: {output_path}')
            self.stdout.write(f'📁 Размер файла: {file_size_mb:.2f} МБ')
            self.stdout.write(f'📊 Данных:')
            self.stdout.write(f'  • Сотрудников: {employees.count()}')
            self.stdout.write(f'  • Записей доступа: {card_accesses.count()}')
            self.stdout.write(f'  • Записей рабочего времени: {worktime_entries.count()}')
            
        except Exception as e:
            self.stdout.write(f'❌ Ошибка создания резервной копии: {e}')
            raise
