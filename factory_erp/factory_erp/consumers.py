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
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def send_initial_data(self):
        """Отправка начальных данных при подключении."""
        await self.send_machine_status()
        await self.send_shift_data()
        await self.send_pulse_data()
    
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
    
    @database_sync_to_async
    def get_machines(self):
        """Получение данных о станках."""
        machines = Machine.objects.all()
        return [
            {
                'id': machine.id,
                'name': machine.name,
                'status': machine.status,
                'current_speed': machine.current_speed,
                'target_speed': machine.target_speed,
                'efficiency': machine.get_efficiency(),
                'last_maintenance': machine.last_maintenance.isoformat() if machine.last_maintenance else None,
            }
            for machine in machines
        ]
    
    @database_sync_to_async
    def get_active_shifts(self):
        """Получение активных смен."""
        shifts = Shift.objects.filter(is_active=True)
        return [
            {
                'id': shift.id,
                'machine': shift.machine.name,
                'start_time': shift.start_time.isoformat(),
                'operator': shift.operator.username if shift.operator else None,
                'target_pulses': shift.target_pulses,
                'current_pulses': shift.get_current_pulses(),
                'efficiency': shift.get_efficiency(),
            }
            for shift in shifts
        ]
    
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
                'speed': pulse.speed,
            }
            for pulse in pulses
        ]
    
    # Групповые сообщения
    async def machine_update(self, event):
        """Обработка обновлений станка."""
        await self.send(text_data=json.dumps({
            'type': 'machine_update',
            'data': event['data']
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
                'name': employee.name,
                'position': employee.position,
                'rfid_uid': employee.rfid_uid,
                'is_active': employee.is_active,
                'last_seen': employee.last_seen.isoformat() if employee.last_seen else None,
            }
            for employee in employees
        ]
    
    @database_sync_to_async
    def get_worktime_data(self):
        """Получение данных о рабочем времени."""
        worktime_entries = WorkTimeEntry.objects.order_by('-entry_time')[:100]
        return [
            {
                'id': entry.id,
                'employee': entry.employee.name,
                'entry_time': entry.entry_time.isoformat(),
                'exit_time': entry.exit_time.isoformat() if entry.exit_time else None,
                'duration': entry.get_duration().total_seconds() if entry.exit_time else None,
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
