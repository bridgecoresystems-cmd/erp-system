# employees/management/commands/create_hr_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from employees.models import Employee, CardAccess

class Command(BaseCommand):
    help = 'Создание групп пользователей для HR системы'

    def handle(self, *args, **options):
        # Получаем типы контента для наших моделей
        employee_ct = ContentType.objects.get_for_model(Employee)
        cardaccess_ct = ContentType.objects.get_for_model(CardAccess)
        
        # Создаем группы пользователей
        groups_permissions = {
            'HR_Admins': {
                'description': 'Полный доступ к HR системе',
                'permissions': [
                    # Права на Employee
                    f'{employee_ct.app_label}.add_employee',
                    f'{employee_ct.app_label}.change_employee',
                    f'{employee_ct.app_label}.delete_employee',
                    f'{employee_ct.app_label}.view_employee',
                    # Права на CardAccess
                    f'{cardaccess_ct.app_label}.add_cardaccess',
                    f'{cardaccess_ct.app_label}.change_cardaccess',
                    f'{cardaccess_ct.app_label}.delete_cardaccess',
                    f'{cardaccess_ct.app_label}.view_cardaccess',
                ]
            },
            'HR_Users': {
                'description': 'Управление сотрудниками без удаления',
                'permissions': [
                    # Права на Employee (без удаления)
                    f'{employee_ct.app_label}.add_employee',
                    f'{employee_ct.app_label}.change_employee',
                    f'{employee_ct.app_label}.view_employee',
                    # Только просмотр доступа
                    f'{cardaccess_ct.app_label}.view_cardaccess',
                ]
            },
            'Security_Users': {
                'description': 'Только просмотр системы контроля доступа',
                'permissions': [
                    # Только просмотр
                    f'{employee_ct.app_label}.view_employee',
                    f'{cardaccess_ct.app_label}.view_cardaccess',
                ]
            },
            'Department_Managers': {
                'description': 'Управление сотрудниками своего отдела',
                'permissions': [
                    # Права на Employee (без добавления и удаления)
                    f'{employee_ct.app_label}.change_employee',
                    f'{employee_ct.app_label}.view_employee',
                    # Просмотр доступа
                    f'{cardaccess_ct.app_label}.view_cardaccess',
                ]
            }
        }
        
        created_groups = 0
        
        for group_name, group_data in groups_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Создана группа: {group_name}')
                )
                created_groups += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'Группа уже существует: {group_name}')
                )
            
            # Добавляем права в группу
            for perm_codename in group_data['permissions']:
                try:
                    app_label, codename = perm_codename.split('.')
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename
                    )
                    group.permissions.add(permission)
                    
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Право не найдено: {perm_codename}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'Обработано групп: {len(groups_permissions)}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Создано новых групп: {created_groups}')
        )
        
        # Показываем инструкцию
        self.stdout.write('\n' + '='*50)
        self.stdout.write('КАК ИСПОЛЬЗОВАТЬ ГРУППЫ:')
        self.stdout.write('='*50)
        self.stdout.write('1. Зайдите в админку: /admin/')
        self.stdout.write('2. Перейдите в "Users" (Пользователи)')
        self.stdout.write('3. Выберите пользователя')
        self.stdout.write('4. В разделе "Groups" добавьте нужную группу:')
        self.stdout.write('   - HR_Admins: полный доступ')
        self.stdout.write('   - HR_Users: управление без удаления')
        self.stdout.write('   - Security_Users: только просмотр')
        self.stdout.write('   - Department_Managers: свой отдел')
        self.stdout.write('5. Сохраните изменения')
        self.stdout.write('='*50)