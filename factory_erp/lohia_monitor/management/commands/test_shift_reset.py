from django.core.management.base import BaseCommand
from lohia_monitor.models import Machine
from lohia_monitor.views import send_websocket_update


class Command(BaseCommand):
    help = 'Тест обнуления метража при завершении смены'

    def handle(self, *args, **kwargs):
        machine = Machine.objects.first()
        
        if not machine:
            self.stdout.write(self.style.ERROR('❌ Станок не найден'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n🏭 Станок: {machine.name}'))
        
        # Показываем текущее состояние
        self.stdout.write(self.style.WARNING('\n📊 До обнуления:'))
        self.stdout.write(f'   Импульсы: {machine.current_pulse_count}')
        self.stdout.write(f'   Метраж: {machine.current_meters:.6f} м')
        self.stdout.write(f'   Оператор: {machine.current_operator or "НЕТ"}')
        
        # Обнуляем как в shift_end_api
        self.stdout.write(self.style.WARNING('\n🔄 Обнуление счетчиков...'))
        
        machine.status = 'idle'
        machine.current_operator = None
        machine.current_pulse_count = 0  # Только импульсы!
        machine.save()  # БЕЗ update_fields
        
        # Перечитываем из БД
        machine.refresh_from_db()
        
        # Показываем результат
        self.stdout.write(self.style.SUCCESS('\n✅ После обнуления:'))
        self.stdout.write(f'   Импульсы: {machine.current_pulse_count}')
        self.stdout.write(f'   Метраж: {machine.current_meters:.6f} м')
        self.stdout.write(f'   Оператор: {machine.current_operator or "НЕТ"}')
        
        # Отправляем WebSocket
        self.stdout.write(self.style.WARNING('\n📡 Отправка WebSocket...'))
        send_websocket_update(machine)
        
        self.stdout.write(self.style.SUCCESS('\n✅ ГОТОВО! Проверьте Dashboard - метраж должен быть 0.0000'))

