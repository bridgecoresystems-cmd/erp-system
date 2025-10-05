# employees/management/commands/generate_reports.py
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import date, timedelta
import csv
import os
from employees.models import Employee, CardAccess, WorkTimeEntry

class Command(BaseCommand):
    help = 'Генерация отчетов по ERP системе'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['daily', 'weekly', 'monthly', 'yearly'],
            default='monthly',
            help='Тип отчета'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Путь для сохранения отчета'
        )

    def handle(self, *args, **options):
        report_type = options['type']
        output_path = options.get('output')
        
        if not output_path:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'report_{report_type}_{timestamp}.csv'
        
        self.stdout.write(f'Генерация {report_type} отчета...')
        
        try:
            # Определяем период
            today = date.today()
            if report_type == 'daily':
                start_date = today
                end_date = today
            elif report_type == 'weekly':
                start_date = today - timedelta(days=7)
                end_date = today
            elif report_type == 'monthly':
                start_date = today.replace(day=1)
                end_date = today
            else:  # yearly
                start_date = today.replace(month=1, day=1)
                end_date = today
            
            # Создаем отчет
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Заголовок
                writer.writerow([
                    'Отчет по ERP системе',
                    f'Период: {start_date} - {end_date}',
                    f'Сгенерирован: {timezone.now().strftime("%d.%m.%Y %H:%M")}'
                ])
                writer.writerow([])
                
                # Общая статистика
                writer.writerow(['ОБЩАЯ СТАТИСТИКА'])
                writer.writerow(['Показатель', 'Значение'])
                
                total_employees = Employee.objects.filter(is_active=True).count()
                writer.writerow(['Активных сотрудников', total_employees])
                
                total_accesses = CardAccess.objects.filter(
                    timestamp__date__range=[start_date, end_date],
                    success=True
                ).count()
                writer.writerow(['Касаний карт', total_accesses])
                
                unique_employees = CardAccess.objects.filter(
                    timestamp__date__range=[start_date, end_date],
                    success=True
                ).values('employee').distinct().count()
                writer.writerow(['Уникальных сотрудников', unique_employees])
                
                # Статистика по отделам
                writer.writerow([])
                writer.writerow(['СТАТИСТИКА ПО ОТДЕЛАМ'])
                writer.writerow(['Отдел', 'Сотрудников', 'Касаний', 'Среднее в день'])
                
                departments = Employee.objects.filter(is_active=True).values('department').annotate(
                    count=Count('id')
                ).order_by('-count')
                
                for dept in departments:
                    dept_name = dept['department']
                    dept_count = dept['count']
                    
                    dept_accesses = CardAccess.objects.filter(
                        employee__department=dept_name,
                        timestamp__date__range=[start_date, end_date],
                        success=True
                    ).count()
                    
                    days = (end_date - start_date).days + 1
                    avg_per_day = dept_accesses / days if days > 0 else 0
                    
                    writer.writerow([dept_name, dept_count, dept_accesses, f'{avg_per_day:.1f}'])
                
                # Статистика рабочего времени
                writer.writerow([])
                writer.writerow(['СТАТИСТИКА РАБОЧЕГО ВРЕМЕНИ'])
                writer.writerow(['Показатель', 'Значение'])
                
                worktime_entries = WorkTimeEntry.objects.filter(
                    date__range=[start_date, end_date]
                )
                
                total_hours = worktime_entries.aggregate(
                    total=Sum('hours_worked')
                )['total'] or 0
                writer.writerow(['Общее время работы (часы)', f'{total_hours:.1f}'])
                
                avg_hours = worktime_entries.aggregate(
                    avg=Avg('hours_worked')
                )['avg'] or 0
                writer.writerow(['Среднее время работы (часы)', f'{avg_hours:.1f}'])
                
                present_days = worktime_entries.filter(status='present').count()
                writer.writerow(['Полных рабочих дней', present_days])
                
                late_days = worktime_entries.filter(status='late').count()
                writer.writerow(['Опозданий', late_days])
                
                # Топ сотрудников по активности
                writer.writerow([])
                writer.writerow(['ТОП-10 САМЫХ АКТИВНЫХ СОТРУДНИКОВ'])
                writer.writerow(['ФИО', 'Отдел', 'Касаний', 'Часов работы'])
                
                top_employees = CardAccess.objects.filter(
                    timestamp__date__range=[start_date, end_date],
                    success=True,
                    employee__is_active=True
                ).values(
                    'employee__first_name',
                    'employee__last_name',
                    'employee__department'
                ).annotate(
                    access_count=Count('id')
                ).order_by('-access_count')[:10]
                
                for emp in top_employees:
                    full_name = f"{emp['employee__last_name']} {emp['employee__first_name']}"
                    dept = emp['employee__department']
                    accesses = emp['access_count']
                    
                    # Получаем часы работы
                    work_hours = WorkTimeEntry.objects.filter(
                        employee__first_name=emp['employee__first_name'],
                        employee__last_name=emp['employee__last_name'],
                        date__range=[start_date, end_date]
                    ).aggregate(total=Sum('hours_worked'))['total'] or 0
                    
                    writer.writerow([full_name, dept, accesses, f'{work_hours:.1f}'])
            
            # Получаем размер файла
            file_size = os.path.getsize(output_path)
            file_size_kb = file_size / 1024
            
            self.stdout.write(f'✅ Отчет создан: {output_path}')
            self.stdout.write(f'📁 Размер файла: {file_size_kb:.1f} КБ')
            self.stdout.write(f'📊 Период: {start_date} - {end_date}')
            
        except Exception as e:
            self.stdout.write(f'❌ Ошибка создания отчета: {e}')
            raise
