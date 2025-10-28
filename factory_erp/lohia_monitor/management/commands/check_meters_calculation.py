from django.core.management.base import BaseCommand
from lohia_monitor.models import Machine


class Command(BaseCommand):
    help = 'Проверка расчета метража'

    def handle(self, *args, **kwargs):
        machine = Machine.objects.first()
        
        if not machine:
            self.stdout.write(self.style.ERROR('❌ Станок не найден'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n🏭 Станок: {machine.name}'))
        self.stdout.write(f'   ESP32 ID: {machine.esp32_id}')
        
        self.stdout.write(self.style.WARNING('\n⚙️  Параметры станка:'))
        self.stdout.write(f'   Transmit Pulse: {machine.transmit_pulse}')
        self.stdout.write(f'   Gear Box Ratio: {machine.gear_box_ratio}')
        self.stdout.write(f'   Sprocket Gear Box: {machine.sprocket_gear_box}')
        self.stdout.write(f'   Sprocket Takeup Roller: {machine.sprocket_takeup_roller}')
        self.stdout.write(f'   Roller Diameter: {machine.roller_diameter_cm} см')
        
        self.stdout.write(self.style.WARNING('\n📊 Расчет:'))
        meters_per_pulse = machine.calculate_meters_per_pulse()
        self.stdout.write(f'   Метров за импульс: {meters_per_pulse:.10f}')
        self.stdout.write(f'   Сохраненный: {machine.meters_per_pulse:.10f}')
        
        self.stdout.write(self.style.WARNING('\n🧪 Тест метража:'))
        
        # Тестовые импульсы
        test_pulses = [1, 10, 45, 100, 115, 1000]
        
        for pulses in test_pulses:
            meters = float(pulses * machine.meters_per_pulse)
            self.stdout.write(f'   {pulses:4d} импульсов → {meters:8.6f} м ({meters:6.2f} м)')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Текущее состояние:'))
        self.stdout.write(f'   Импульсы: {machine.current_pulse_count}')
        self.stdout.write(f'   Метраж: {machine.current_meters:.6f} м')
        self.stdout.write(f'   Оператор: {machine.current_operator or "НЕТ"}')

