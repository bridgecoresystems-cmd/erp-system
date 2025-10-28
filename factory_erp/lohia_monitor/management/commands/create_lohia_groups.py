from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from lohia_monitor.models import Machine, Shift, MaintenanceCall


class Command(BaseCommand):
    help = 'Создает группы Lohia: Operator и Master, и назначает права'

    def handle(self, *args, **options):
        self.stdout.write('Создание групп Lohia...')

        machine_ct = ContentType.objects.get_for_model(Machine)
        shift_ct = ContentType.objects.get_for_model(Shift)
        maintenance_ct = ContentType.objects.get_for_model(MaintenanceCall)

        # Наборы прав
        operator_perm_codenames = [
            # Machine: только просмотр
            ('view_machine', machine_ct),

            # Shift: создавать старт/стоп (add/change для фиксации текущей смены), и просмотр
            ('add_shift', shift_ct),
            ('change_shift', shift_ct),
            ('view_shift', shift_ct),

            # MaintenanceCall: создавать вызов, просматривать
            ('add_maintenancecall', maintenance_ct),
            ('view_maintenancecall', maintenance_ct),
        ]

        master_perm_codenames = [
            # Machine: просмотр
            ('view_machine', machine_ct),

            # Shift: просмотр (мастер не открывает/закрывает смены)
            ('view_shift', shift_ct),

            # MaintenanceCall: просмотр и изменение статуса (start/end)
            ('view_maintenancecall', maintenance_ct),
            ('change_maintenancecall', maintenance_ct),
        ]

        groups = {
            'Lohia_Operator': operator_perm_codenames,
            'Lohia_Master': master_perm_codenames,
        }

        for group_name, perms in groups.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Создана группа: {group_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'ℹ️ Группа уже существует: {group_name}'))

            added = 0
            for codename, ct in perms:
                try:
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    group.permissions.add(perm)
                    added += 1
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Право не найдено: {codename} ({ct.app_label})'))

            self.stdout.write(f'  📋 Добавлено прав: {added}')

        self.stdout.write(self.style.SUCCESS('✅ Группы Lohia созданы/обновлены'))


