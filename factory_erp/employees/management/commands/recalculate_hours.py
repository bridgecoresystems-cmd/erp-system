from django.core.management.base import BaseCommand
from employees.models import WorkTimeEntry

class Command(BaseCommand):
    help = 'Пересчитывает часы для всех записей рабочего времени'

    def handle(self, *args, **options):
        entries = WorkTimeEntry.objects.filter(
            entry_time__isnull=False,
            exit_time__isnull=False
        )
        
        updated_count = 0
        for entry in entries:
            old_hours = entry.hours_worked
            new_hours = entry.calculate_hours_worked()
            
            if old_hours != new_hours:
                entry.hours_worked = new_hours
                entry.save()
                updated_count += 1
                
                self.stdout.write(
                    f"Обновлено: {entry.employee.get_full_name()} "
                    f"({entry.date}) {old_hours}ч → {new_hours}ч"
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно обновлено {updated_count} записей'
            )
        )