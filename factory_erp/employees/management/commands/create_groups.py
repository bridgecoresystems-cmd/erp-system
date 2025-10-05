# employees/management/commands/create_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Создание групп пользователей для ERP системы'

    def handle(self, *args, **options):
        self.stdout.write('Создание групп пользователей...')
        
        # Определяем группы и их права
        groups_data = {
            'HR_Admins': {
                'description': 'HR администраторы - полный доступ к сотрудникам',
                'permissions': [
                    'employees.add_employee',
                    'employees.change_employee', 
                    'employees.delete_employee',
                    'employees.view_employee',
                    'employees.add_worktimeentry',
                    'employees.change_worktimeentry',
                    'employees.delete_worktimeentry',
                    'employees.view_worktimeentry',
                ]
            },
            'HR_Users': {
                'description': 'HR пользователи - просмотр и редактирование рабочего времени',
                'permissions': [
                    'employees.view_employee',
                    'employees.add_worktimeentry',
                    'employees.change_worktimeentry',
                    'employees.view_worktimeentry',
                ]
            },
            'Security': {
                'description': 'Служба безопасности - полный доступ к системе безопасности',
                'permissions': [
                    'security.view_dashboard',
                    'security.add_shift',
                    'security.change_shift',
                    'security.view_shift',
                    'employees.view_employee',
                    'employees.view_cardaccess',
                ]
            },
            'Security_Users': {
                'description': 'Пользователи безопасности - просмотр экрана доступа',
                'permissions': [
                    'employees.view_employee',
                    'employees.view_cardaccess',
                ]
            },
        }
        
        created_count = 0
        updated_count = 0
        
        for group_name, group_info in groups_data.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(f'✅ Создана группа: {group_name}')
                created_count += 1
            else:
                self.stdout.write(f'ℹ️ Группа уже существует: {group_name}')
                updated_count += 1
            
            # Добавляем права доступа
            permissions_added = 0
            for perm_codename in group_info['permissions']:
                try:
                    app_label, codename = perm_codename.split('.', 1)
                    # Ищем права по коду, игнорируя app_label для избежания конфликтов
                    permission = Permission.objects.filter(codename=codename).first()
                    if permission:
                        group.permissions.add(permission)
                        permissions_added += 1
                    else:
                        self.stdout.write(f'⚠️ Право не найдено: {perm_codename}')
                except ValueError:
                    self.stdout.write(f'⚠️ Неверный формат права: {perm_codename}')
            
            if permissions_added > 0:
                self.stdout.write(f'  📋 Добавлено прав: {permissions_added}')
        
        self.stdout.write(f'\n📊 Результат:')
        self.stdout.write(f'  • Создано новых групп: {created_count}')
        self.stdout.write(f'  • Обновлено существующих: {updated_count}')
        self.stdout.write(f'  • Всего групп: {len(groups_data)}')
        
        self.stdout.write('\n✅ Группы пользователей созданы успешно!')
        self.stdout.write('\n💡 Теперь назначьте пользователей в соответствующие группы через админку Django.')
