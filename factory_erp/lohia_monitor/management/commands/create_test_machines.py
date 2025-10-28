# lohia_monitor/management/commands/create_test_machines.py
from django.core.management.base import BaseCommand
from lohia_monitor.models import Machine


class Command(BaseCommand):
    help = 'Создает тестовые станки для демонстрации dashboard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Количество станков для создания (по умолчанию 10)',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(self.style.SUCCESS(f'Создание {count} тестовых станков...'))
        
        created = 0
        for i in range(1, count + 1):
            machine_name = f"Lohia №{i}"
            esp32_id = f"ESP32_LOHIA_{i:03d}"
            
            # Проверяем, не существует ли уже станок с таким ESP32 ID
            if Machine.objects.filter(esp32_id=esp32_id).exists():
                self.stdout.write(self.style.WARNING(f'Станок {machine_name} уже существует, пропускаем'))
                continue
            
            # Создаем станок
            machine = Machine.objects.create(
                name=machine_name,
                esp32_id=esp32_id,
                transmit_pulse=40,
                gear_box_ratio=64.00,
                sprocket_gear_box=23,
                sprocket_takeup_roller=41,
                roller_diameter_cm=16.70,
                p_ctrl_ampl=2,
                is_active=True,
                status='idle',
            )
            
            created += 1
            self.stdout.write(self.style.SUCCESS(f'✓ Создан станок: {machine_name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nВсего создано станков: {created}'))
        self.stdout.write(self.style.SUCCESS('Dashboard готов к просмотру!'))

