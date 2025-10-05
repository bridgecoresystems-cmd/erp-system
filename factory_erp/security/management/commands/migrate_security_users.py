from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User


class Command(BaseCommand):
    help = 'Миграция пользователей из группы Security_Users в Security'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, что будет сделано, без выполнения изменений',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        try:
            old_group = Group.objects.get(name='Security_Users')
            new_group, created = Group.objects.get_or_create(name='Security')
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Создана новая группа "Security"')
                )
            
            # Получаем пользователей из старой группы
            users_to_migrate = old_group.user_set.all()
            
            if not users_to_migrate:
                self.stdout.write(
                    self.style.WARNING('Пользователей в группе Security_Users не найдено')
                )
                return
            
            self.stdout.write(f'Найдено {users_to_migrate.count()} пользователей для миграции:')
            
            for user in users_to_migrate:
                self.stdout.write(f'  - {user.username} ({user.get_full_name()})')
                
                if not dry_run:
                    # Добавляем в новую группу
                    new_group.user_set.add(user)
                    # Удаляем из старой группы
                    old_group.user_set.remove(user)
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('Это был пробный запуск. Для выполнения миграции запустите команду без --dry-run')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Успешно мигрировано {users_to_migrate.count()} пользователей из Security_Users в Security')
                )
                
                # Удаляем старую группу если она пустая
                if old_group.user_set.count() == 0:
                    old_group.delete()
                    self.stdout.write(
                        self.style.SUCCESS('Пустая группа Security_Users была удалена')
                    )
                
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Группа Security_Users не найдена')
            )