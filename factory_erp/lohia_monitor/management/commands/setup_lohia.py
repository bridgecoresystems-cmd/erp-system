# lohia_monitor/management/commands/setup_lohia.py
from django.core.management.base import BaseCommand
from lohia_monitor.models import Machine
from employees.models import Employee

class Command(BaseCommand):
    help = 'Настройка системы мониторинга станка Lohia'

    def handle(self, *args, **options):
        self.stdout.write('Настройка системы мониторинга станка Lohia...')
        
        # Создаем станок Lohia
        machine, created = Machine.objects.get_or_create(
            esp32_id='LOHIA-001',
            defaults={
                'name': 'Станок Lohia #1',
                'meters_per_pulse': 0.500,  # 0.5 метра за импульс
                'is_active': True,
                'status': 'idle',
            }
        )
        
        if created:
            self.stdout.write(f'✅ Создан станок: {machine.name}')
        else:
            self.stdout.write(f'ℹ️ Станок уже существует: {machine.name}')
        
        # Проверяем сотрудников
        operators = Employee.objects.filter(department='Сотрудник_bag', is_active=True)
        masters = Employee.objects.filter(department='Механики', is_active=True)
        supervisors = Employee.objects.filter(department='Начальник_цеха', is_active=True)
        
        self.stdout.write(f'\n📊 Статистика сотрудников:')
        self.stdout.write(f'  • Операторов: {operators.count()}')
        self.stdout.write(f'  • Мастеров: {masters.count()}')
        self.stdout.write(f'  • Начальников цеха: {supervisors.count()}')
        
        if operators.count() == 0:
            self.stdout.write('\n⚠️ Нет операторов с отделом "Сотрудник_bag"')
            self.stdout.write('   Создайте сотрудника с этим отделом для тестирования')
        
        if masters.count() == 0:
            self.stdout.write('\n⚠️ Нет мастеров с отделом "Механики"')
            self.stdout.write('   Создайте сотрудника с этим отделом для тестирования')
        
        if supervisors.count() == 0:
            self.stdout.write('\n⚠️ Нет начальников цеха с отделом "Начальник_цеха"')
            self.stdout.write('   Создайте сотрудника с этим отделом для тестирования')
        
        self.stdout.write(f'\n🔧 Настройка ESP32:')
        self.stdout.write(f'  • device_id: LOHIA-001')
        self.stdout.write(f'  • URL: /lohia/api/shift/start/')
        self.stdout.write(f'  • JSON: {{"esp32_id": "LOHIA-001", "rfid_uid": "XXXX"}}')
        
        self.stdout.write(f'\n📱 API Endpoints:')
        self.stdout.write(f'  • Начало смены: POST /lohia/api/shift/start/')
        self.stdout.write(f'  • Окончание смены: POST /lohia/api/shift/end/')
        self.stdout.write(f'  • Обновление импульсов: POST /lohia/api/pulse/update/')
        self.stdout.write(f'  • Вызов мастера: POST /lohia/api/maintenance/call/')
        self.stdout.write(f'  • Начало ремонта: POST /lohia/api/maintenance/start/')
        self.stdout.write(f'  • Завершение ремонта: POST /lohia/api/maintenance/end/')
        
        self.stdout.write(f'\n🌐 Веб-интерфейс:')
        self.stdout.write(f'  • Дашборд: /lohia/dashboard/')
        self.stdout.write(f'  • История смен: /lohia/shifts/')
        self.stdout.write(f'  • История вызовов: /lohia/maintenance/')
        self.stdout.write(f'  • Статистика: /lohia/stats/')
        
        self.stdout.write('\n✅ Система мониторинга Lohia настроена!')
