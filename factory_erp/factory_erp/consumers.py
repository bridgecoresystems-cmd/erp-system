"""
WebSocket consumers for factory_erp project.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from lohia_monitor.models import Machine, Shift, PulseLog
from employees.models import Employee, WorkTimeEntry
import asyncio
from datetime import datetime


class LohiaConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer для мониторинга станка Lohia."""
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'lohia_{self.room_name}'
        
        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Отправляем начальные данные
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        # Покидаем группу
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Обработка сообщений от клиента."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_machine_status':
                await self.send_machine_status()
            elif message_type == 'get_shift_data':
                await self.send_shift_data()
            elif message_type == 'get_pulse_data':
                await self.send_pulse_data()
            elif message_type == 'get_maintenance_data':
                await self.send_maintenance_data()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def send_initial_data(self):
        """Отправка начальных данных при подключении."""
        # Отправляем ПОЛНЫЕ данные о станках
        machines = await self.get_machines()
        await self.send(text_data=json.dumps({
            'type': 'machine_status',
            'data': machines
        }))
    
    async def send_machine_status(self):
        """Отправка статуса станка."""
        machines = await self.get_machines()
        await self.send(text_data=json.dumps({
            'type': 'machine_status',
            'data': machines
        }))
    
    async def send_shift_data(self):
        """Отправка данных о сменах."""
        shifts = await self.get_active_shifts()
        await self.send(text_data=json.dumps({
            'type': 'shift_data',
            'data': shifts
        }))
    
    async def send_pulse_data(self):
        """Отправка данных о пульсах."""
        pulses = await self.get_recent_pulses()
        await self.send(text_data=json.dumps({
            'type': 'pulse_data',
            'data': pulses
        }))
    
    async def send_maintenance_data(self):
        """Отправка данных о вызовах мастера."""
        maintenance_calls = await self.get_maintenance_calls()
        await self.send(text_data=json.dumps({
            'type': 'maintenance_data',
            'data': maintenance_calls
        }))
    
    @database_sync_to_async
    def get_machines(self):
        """Получение ПОЛНЫХ данных о станках для dashboard."""
        from lohia_monitor.models import Machine, MaintenanceCall
        import logging
        logger = logging.getLogger(__name__)
        
        machines = Machine.objects.filter(is_active=True).select_related('current_operator').order_by('id')
        result = []
        
        for machine in machines:
            # Активный вызов мастера
            active_call = MaintenanceCall.objects.filter(
                machine=machine, 
                status__in=['pending', 'in_progress']
            ).select_related('master', 'operator').first()
            
            item = {
                'machine_id': machine.id,
                'name': machine.name,
                'status': machine.status,
                # ВАЖНО: Всегда отправляем имя оператора если он есть
                'current_operator': machine.current_operator.get_full_name() if machine.current_operator else None,
                'current_pulse_count': machine.current_pulse_count,
                'current_meters': float(machine.current_meters),
                'meters_per_pulse': float(machine.meters_per_pulse),
                # Данные о вызове мастера
                'call_status': active_call.status if active_call else None,
                'call_operator': active_call.operator.get_full_name() if active_call and active_call.operator else None,
                'master': active_call.master.get_full_name() if active_call and active_call.master else None,
            }
            result.append(item)
            logger.debug(f"Consumer sending data for {machine.name}: meters={machine.current_meters}, operator={item['current_operator']}")
        
        return result
    
    @database_sync_to_async
    def get_recent_pulses(self):
        """Получение последних пульсов."""
        pulses = PulseLog.objects.order_by('-timestamp')[:50]
        return [
            {
                'id': pulse.id,
                'machine': pulse.machine.name,
                'timestamp': pulse.timestamp.isoformat(),
                'pulse_count': pulse.pulse_count,
                'meters_produced': float(pulse.meters_produced),
            }
            for pulse in pulses
        ]
    
    @database_sync_to_async
    def get_maintenance_calls(self):
        """Получение данных о вызовах мастера."""
        # Пока возвращаем пустой список, так как модель MaintenanceCall может не существовать
        # В будущем можно добавить реальную модель для вызовов мастера
        return []
    
    # Групповые сообщения
    async def machine_update(self, event):
        """Обработка обновлений станка - читаем данные из БД и отправляем."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Небольшая задержка чтобы БД точно обновилась после транзакции
        await asyncio.sleep(0.2)
        
        # Читаем СВЕЖИЕ данные из БД
        machines = await self.get_machines()
        
        logger.info(f"📡 Consumer machine_update: отправка {len(machines)} станков")
        for m in machines:
            logger.info(f"  → {m['name']}: pulses={m['current_pulse_count']}, meters={m['current_meters']:.6f}, operator={m['current_operator']}")
        
        # Отправляем полные данные клиенту
        await self.send(text_data=json.dumps({
            'type': 'machine_status',
            'data': machines
        }))
    
    async def shift_update(self, event):
        """Обработка обновлений смены."""
        await self.send(text_data=json.dumps({
            'type': 'shift_update',
            'data': event['data']
        }))
    
    async def pulse_update(self, event):
        """Обработка обновлений пульсов."""
        await self.send(text_data=json.dumps({
            'type': 'pulse_update',
            'data': event['data']
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer для общих уведомлений."""
    
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            self.group_name = f'notifications_{self.user.id}'
            
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            await self.accept()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Обработка сообщений от клиента."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Отметить уведомление как прочитанное."""
        # Здесь можно добавить логику для отметки уведомлений
        pass
    
    async def notification_message(self, event):
        """Отправка уведомления."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))


class EmployeeConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer для мониторинга сотрудников."""
    
    async def connect(self):
        self.group_name = 'employees_monitor'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        await self.send_employee_data()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Обработка сообщений от клиента."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_employee_data':
                await self.send_employee_data()
            elif message_type == 'get_worktime_data':
                await self.send_worktime_data()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def send_employee_data(self):
        """Отправка данных о сотрудниках."""
        employees = await self.get_employees()
        await self.send(text_data=json.dumps({
            'type': 'employee_data',
            'data': employees
        }))
    
    async def send_worktime_data(self):
        """Отправка данных о рабочем времени."""
        worktime = await self.get_worktime_data()
        await self.send(text_data=json.dumps({
            'type': 'worktime_data',
            'data': worktime
        }))
    
    @database_sync_to_async
    def get_employees(self):
        """Получение данных о сотрудниках."""
        employees = Employee.objects.all()
        return [
            {
                'id': employee.id,
                'name': employee.get_full_name() if hasattr(employee, 'get_full_name') else f"{getattr(employee, 'last_name', '')} {getattr(employee, 'first_name', '')}".strip(),
                'position': employee.position,
                'rfid_uid': employee.rfid_uid,
                'is_active': employee.is_active,
                # Поля last_seen может не быть в модели; отдаем None
                'last_seen': None,
            }
            for employee in employees
        ]
    
    @database_sync_to_async
    def get_worktime_data(self):
        """Получение данных о рабочем времени."""
        from django.utils import timezone
        worktime_entries = WorkTimeEntry.objects.order_by('-entry_time')[:100]
        return [
            {
                'id': entry.id,
                'employee': entry.employee.get_full_name() if hasattr(entry.employee, 'get_full_name') else f"{getattr(entry.employee, 'last_name', '')} {getattr(entry.employee, 'first_name', '')}".strip(),
                'entry_time': timezone.make_aware(datetime.combine(entry.date, entry.entry_time)).isoformat() if entry.entry_time else None,
                'exit_time': timezone.make_aware(datetime.combine(entry.date, entry.exit_time)).isoformat() if entry.exit_time else None,
                'duration': int(float(entry.hours_worked) * 3600) if entry.hours_worked else None,
            }
            for entry in worktime_entries
        ]
    
    async def employee_update(self, event):
        """Обработка обновлений сотрудников."""
        await self.send(text_data=json.dumps({
            'type': 'employee_update',
            'data': event['data']
        }))
    
    async def worktime_update(self, event):
        """Обработка обновлений рабочего времени."""
        await self.send(text_data=json.dumps({
            'type': 'worktime_update',
            'data': event['data']
        }))


class SecurityConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer для мониторинга безопасности."""
    
    async def connect(self):
        self.group_name = 'security_monitor'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        await self.send_security_data()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Обработка сообщений от клиента."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_security_data':
                await self.send_security_data()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def send_security_data(self):
        """Отправка данных о безопасности."""
        security_data = await self.get_security_data()
        await self.send(text_data=json.dumps({
            'type': 'security_data',
            'data': security_data
        }))
    
    @database_sync_to_async
    def get_security_data(self):
        """Получение данных о безопасности."""
        # Здесь можно добавить логику для получения данных о безопасности
        return {
            'active_users': 0,
            'security_events': [],
            'system_status': 'normal'
        }
    
    async def security_update(self, event):
        """Обработка обновлений безопасности."""
        await self.send(text_data=json.dumps({
            'type': 'security_update',
            'data': event['data']
        }))
    
    async def maintenance_call_update(self, event):
        """Обработка обновлений вызова мастера - отправляем ВСЕ данные заново."""
        # Вместо отправки частичных данных, отправляем полный статус
        machines = await self.get_machines()
        await self.send(text_data=json.dumps({
            'type': 'machine_status',
            'data': machines
        }))
