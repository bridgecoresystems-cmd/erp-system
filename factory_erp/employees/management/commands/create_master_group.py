# employees/management/commands/create_master_group.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Создает группу "Мастера" если её нет'

    def handle(self, *args, **options):
        group_name = 'Мастера'
        
        group, created = Group.objects.get_or_create(name=group_name)
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Группа "{group_name}" создана'))
        else:
            self.stdout.write(self.style.WARNING(f'Группа "{group_name}" уже существует'))
        
        # Показываем количество пользователей в группе
        count = group.user_set.count()
        self.stdout.write(self.style.SUCCESS(f'Пользователей в группе: {count}'))
        
        if count > 0:
            self.stdout.write('\nМастера:')
            for user in group.user_set.all():
                self.stdout.write(f'  - {user.username} ({user.get_full_name() if hasattr(user, "get_full_name") else ""})')

