# lohia_monitor/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.db import models
import json
import logging

from .models import Machine, Shift, MaintenanceCall, PulseLog
from employees.models import Employee

logger = logging.getLogger(__name__)

# ===== API ENDPOINTS ДЛЯ ESP32 =====

@csrf_exempt
@require_http_methods(["POST"])
def shift_start_api(request):
    """API для начала смены"""
    try:
        data = json.loads(request.body)
        esp32_id = data.get('esp32_id')
        rfid_uid = data.get('rfid_uid')
        
        logger.info(f"Shift start request: esp32_id={esp32_id}, rfid_uid='{rfid_uid}'")
        
        # Находим станок
        machine = get_object_or_404(Machine, esp32_id=esp32_id, is_active=True)
        
        # Находим оператора
        try:
            operator = Employee.objects.get(rfid_uid__iexact=rfid_uid, is_active=True)
            logger.info(f"Found operator: {operator.get_full_name()} with RFID: '{operator.rfid_uid}'")
        except Employee.DoesNotExist:
            logger.error(f"Employee not found with RFID: '{rfid_uid}'")
            return JsonResponse({
                'success': False,
                'error': f'Сотрудник с RFID {rfid_uid} не найден'
            }, status=400)
        
        # Проверяем, что оператор может работать на этом станке
        if machine.current_operator and machine.current_operator != operator:
            return JsonResponse({
                'success': False,
                'error': f'Станок уже занят оператором {machine.current_operator.get_full_name()}'
            }, status=400)
        
        # Завершаем предыдущую смену, если есть
        if machine.current_operator:
            active_shift = Shift.objects.filter(
                machine=machine, 
                operator=machine.current_operator, 
                status='active'
            ).first()
            if active_shift:
                active_shift.complete_shift()
        
        # Начинаем новую смену
        machine.start_shift(operator)
        shift = Shift.objects.create(
            operator=operator,
            machine=machine,
            start_time=timezone.now()
        )
        
        logger.info(f"Shift started: {operator.get_full_name()} on {machine.name}")
        
        return JsonResponse({
            'success': True,
            'message': f'Смена начата: {operator.get_full_name()}',
            'shift_id': shift.id,
            'machine': {
                'name': machine.name,
                'status': machine.status
            }
        })
        
    except Exception as e:
        logger.error(f"Error in shift_start_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def shift_end_api(request):
    """API для окончания смены"""
    try:
        data = json.loads(request.body)
        esp32_id = data.get('esp32_id')
        rfid_uid = data.get('rfid_uid')
        
        logger.info(f"Shift end request: esp32_id={esp32_id}, rfid_uid='{rfid_uid}'")
        
        # Находим станок
        machine = get_object_or_404(Machine, esp32_id=esp32_id, is_active=True)
        
        # Находим оператора
        try:
            operator = Employee.objects.get(rfid_uid__iexact=rfid_uid, is_active=True)
            logger.info(f"Found operator: {operator.get_full_name()} with RFID: '{operator.rfid_uid}'")
        except Employee.DoesNotExist:
            logger.error(f"Employee not found with RFID: '{rfid_uid}'")
            return JsonResponse({
                'success': False,
                'error': f'Сотрудник с RFID {rfid_uid} не найден'
            }, status=400)
        
        # Проверяем, что оператор работает на этом станке
        if machine.current_operator != operator:
            return JsonResponse({
                'success': False,
                'error': 'Вы не работаете на этом станке'
            }, status=400)
        
        # Завершаем смену
        active_shift = Shift.objects.filter(
            machine=machine, 
            operator=operator, 
            status='active'
        ).first()
        
        if active_shift:
            active_shift.total_pulses = machine.current_pulse_count
            active_shift.total_meters = machine.current_meters
            active_shift.complete_shift()
        
        machine.end_shift()
        
        logger.info(f"Shift ended: {operator.get_full_name()} on {machine.name}")
        
        return JsonResponse({
            'success': True,
            'message': f'Смена завершена: {operator.get_full_name()}',
            'shift': {
                'total_pulses': active_shift.total_pulses if active_shift else 0,
                'total_meters': float(active_shift.total_meters) if active_shift else 0,
                'duration_hours': active_shift.duration_hours if active_shift else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error in shift_end_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def pulse_update_api(request):
    """API для обновления счетчика импульсов"""
    try:
        data = json.loads(request.body)
        esp32_id = data.get('esp32_id')
        pulse_count = data.get('pulse_count', 0)
        
        # Находим станок
        machine = get_object_or_404(Machine, esp32_id=esp32_id, is_active=True)
        
        # Проверяем, что станок работает
        if not machine.current_operator:
            return JsonResponse({
                'success': False,
                'error': 'Станок не работает'
            }, status=400)
        
        # Обновляем счетчик
        machine.current_pulse_count += pulse_count
        machine.save()
        
        # Находим активную смену
        active_shift = Shift.objects.filter(
            machine=machine, 
            operator=machine.current_operator, 
            status='active'
        ).first()
        
        if active_shift:
            # Создаем лог импульсов
            PulseLog.objects.create(
                machine=machine,
                shift=active_shift,
                timestamp=timezone.now(),
                pulse_count=pulse_count,
                total_pulses=machine.current_pulse_count,
                meters_produced=machine.current_meters
            )
            
            # Обновляем смену
            active_shift.total_pulses = machine.current_pulse_count
            active_shift.total_meters = machine.current_meters
            active_shift.save()
        
        return JsonResponse({
            'success': True,
            'total_pulses': machine.current_pulse_count,
            'total_meters': float(machine.current_meters)
        })
        
    except Exception as e:
        logger.error(f"Error in pulse_update_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def maintenance_call_api(request):
    """API для вызова мастера"""
    try:
        data = json.loads(request.body)
        esp32_id = data.get('esp32_id')
        
        # Находим станок
        machine = get_object_or_404(Machine, esp32_id=esp32_id, is_active=True)
        
        # Проверяем, что есть оператор
        if not machine.current_operator:
            return JsonResponse({
                'success': False,
                'error': 'Нет оператора на станке'
            }, status=400)
        
        # Проверяем, нет ли уже активного вызова
        active_call = MaintenanceCall.objects.filter(
            machine=machine, 
            status__in=['pending', 'in_progress']
        ).first()
        
        if active_call:
            return JsonResponse({
                'success': False,
                'error': 'Уже есть активный вызов мастера'
            }, status=400)
        
        # Создаем вызов
        call = MaintenanceCall.objects.create(
            machine=machine,
            operator=machine.current_operator,
            call_time=timezone.now()
        )
        
        logger.info(f"Maintenance call created: {machine.name} by {machine.current_operator.get_full_name()}")
        
        return JsonResponse({
            'success': True,
            'message': 'Мастер вызван',
            'call_id': call.id
        })
        
    except Exception as e:
        logger.error(f"Error in maintenance_call_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def maintenance_start_api(request):
    """API для начала ремонта"""
    try:
        data = json.loads(request.body)
        esp32_id = data.get('esp32_id')
        rfid_uid = data.get('rfid_uid')
        
        # Находим станок
        machine = get_object_or_404(Machine, esp32_id=esp32_id, is_active=True)
        
        # Находим мастера
        master = get_object_or_404(Employee, rfid_uid__iexact=rfid_uid, is_active=True)
        
        # Находим активный вызов
        active_call = MaintenanceCall.objects.filter(
            machine=machine, 
            status='pending'
        ).first()
        
        if not active_call:
            return JsonResponse({
                'success': False,
                'error': 'Нет активного вызова мастера'
            }, status=400)
        
        # Начинаем ремонт
        active_call.start_maintenance(master)
        
        logger.info(f"Maintenance started: {master.get_full_name()} on {machine.name}")
        
        return JsonResponse({
            'success': True,
            'message': f'Ремонт начат мастером {master.get_full_name()}',
            'call_id': active_call.id
        })
        
    except Exception as e:
        logger.error(f"Error in maintenance_start_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def maintenance_end_api(request):
    """API для завершения ремонта"""
    try:
        data = json.loads(request.body)
        esp32_id = data.get('esp32_id')
        rfid_uid = data.get('rfid_uid')
        description = data.get('description', '')
        
        # Находим станок
        machine = get_object_or_404(Machine, esp32_id=esp32_id, is_active=True)
        
        # Находим мастера
        master = get_object_or_404(Employee, rfid_uid__iexact=rfid_uid, is_active=True)
        
        # Находим активный вызов
        active_call = MaintenanceCall.objects.filter(
            machine=machine, 
            status='in_progress',
            master=master
        ).first()
        
        if not active_call:
            return JsonResponse({
                'success': False,
                'error': 'Нет активного ремонта для этого мастера'
            }, status=400)
        
        # Завершаем ремонт
        active_call.complete_maintenance(description)
        
        logger.info(f"Maintenance completed: {master.get_full_name()} on {machine.name}")
        
        return JsonResponse({
            'success': True,
            'message': f'Ремонт завершен мастером {master.get_full_name()}',
            'call_id': active_call.id,
            'repair_time': str(active_call.repair_time) if active_call.repair_time else None
        })
        
    except Exception as e:
        logger.error(f"Error in maintenance_end_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# ===== ВЕБ-ИНТЕРФЕЙС ДЛЯ НАЧАЛЬНИКА ЦЕХА =====

class DashboardView(TemplateView):
    """Дашборд реального времени"""
    template_name = 'lohia_monitor/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем станок (пока один)
        machine = Machine.objects.filter(is_active=True).first()
        
        if machine:
            # Активная смена
            active_shift = Shift.objects.filter(
                machine=machine, 
                status='active'
            ).first()
            
            # Активный вызов мастера
            active_call = MaintenanceCall.objects.filter(
                machine=machine, 
                status__in=['pending', 'in_progress']
            ).first()
            
            # Последние импульсы (для графика)
            recent_pulses = PulseLog.objects.filter(
                machine=machine
            ).order_by('-timestamp')[:20]
            
            context.update({
                'machine': machine,
                'active_shift': active_shift,
                'active_call': active_call,
                'recent_pulses': recent_pulses,
            })
        
        return context

class ShiftsHistoryView(TemplateView):
    """История смен"""
    template_name = 'lohia_monitor/shifts_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        shifts = Shift.objects.all().select_related('operator', 'machine')
        context['shifts'] = shifts
        
        return context

class MaintenanceHistoryView(TemplateView):
    """История вызовов мастера"""
    template_name = 'lohia_monitor/maintenance_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        calls = MaintenanceCall.objects.all().select_related('operator', 'master', 'machine')
        context['calls'] = calls
        
        return context

class MachineStatsView(TemplateView):
    """Статистика станка"""
    template_name = 'lohia_monitor/machine_stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        machine = Machine.objects.filter(is_active=True).first()
        
        if machine:
            # Общая статистика
            total_shifts = Shift.objects.filter(machine=machine).count()
            total_meters = Shift.objects.filter(machine=machine).aggregate(
                total=models.Sum('total_meters')
            )['total'] or 0
            
            total_calls = MaintenanceCall.objects.filter(machine=machine).count()
            
            # Вычисляем среднее время реакции вручную
            completed_calls = MaintenanceCall.objects.filter(
                machine=machine, 
                start_time__isnull=False
            )
            
            if completed_calls.exists():
                total_response_seconds = 0
                count = 0
                for call in completed_calls:
                    if call.response_time:
                        total_response_seconds += call.response_time.total_seconds()
                        count += 1
                
                avg_response_time = total_response_seconds / count / 60 if count > 0 else 0  # в минутах
            else:
                avg_response_time = 0
            
            # Вычисляем среднюю производительность за смену
            avg_meters_per_shift = float(total_meters) / total_shifts if total_shifts > 0 else 0
            
            # Вычисляем эффективность (вызовы на смену)
            calls_per_shift = total_calls / total_shifts if total_shifts > 0 else 0
            
            context.update({
                'machine': machine,
                'total_shifts': total_shifts,
                'total_meters': total_meters,
                'total_calls': total_calls,
                'avg_response_time': avg_response_time,
                'avg_meters_per_shift': avg_meters_per_shift,
                'calls_per_shift': calls_per_shift,
            })
        
        return context


# ===== API ДЛЯ AJAX ОБНОВЛЕНИЯ =====

@require_http_methods(["GET"])
def dashboard_status_api(request):
    """API для получения текущего статуса дашборда (AJAX polling)"""
    try:
        machine = Machine.objects.filter(is_active=True).first()
        
        if not machine:
            return JsonResponse({'success': False, 'error': 'No machine found'}, status=404)
        
        # Активная смена
        active_shift = Shift.objects.filter(
            machine=machine, 
            status='active'
        ).select_related('operator').first()
        
        # Активный вызов мастера
        active_call = MaintenanceCall.objects.filter(
            machine=machine, 
            status__in=['pending', 'in_progress']
        ).select_related('operator', 'master').first()
        
        response_data = {
            'success': True,
            'machine': {
                'name': machine.name,
                'status': machine.status,
                'current_operator': machine.current_operator.get_full_name() if machine.current_operator else None,
                'current_pulse_count': machine.current_pulse_count,
                'current_meters': float(machine.current_meters),
            },
            'active_shift': None,
            'active_call': None,
        }
        
        if active_shift:
            response_data['active_shift'] = {
                'operator': active_shift.operator.get_full_name(),
                'start_time': timezone.localtime(active_shift.start_time).strftime('%H:%M'),
                'duration_hours': active_shift.duration_hours,
                'total_pulses': active_shift.total_pulses,
                'total_meters': float(active_shift.total_meters),
            }
        
        if active_call:
            response_data['active_call'] = {
                'status': active_call.status,
                'status_display': active_call.get_status_display(),
                'operator': active_call.operator.get_full_name(),
                'master': active_call.master.get_full_name() if active_call.master else None,
                'call_time': timezone.localtime(active_call.call_time).strftime('%H:%M'),
                'response_time': str(active_call.response_time) if active_call.response_time else None,
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in dashboard_status_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def maintenance_history_api(request):
    """API для получения обновленной истории вызовов мастера"""
    try:
        calls = MaintenanceCall.objects.select_related('operator', 'master', 'machine').order_by('-call_time')[:20]
        
        calls_data = []
        for call in calls:
            calls_data.append({
                'id': call.id,
                'call_time': timezone.localtime(call.call_time).strftime('%d.%m.%Y %H:%M:%S'),
                'operator': call.operator.get_full_name() if call.operator else 'Неизвестно',
                'master': call.master.get_full_name() if call.master else 'Не назначен',
                'status': call.get_status_display(),
                'response_time': call.get_response_time_display(),
                'repair_time': call.get_repair_time_display(),
            })
        
        return JsonResponse({'success': True, 'calls': calls_data})
        
    except Exception as e:
        logger.error(f"Error in maintenance_history_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def shifts_history_api(request):
    """API для получения обновленной истории смен"""
    try:
        shifts = Shift.objects.select_related('operator', 'machine').order_by('-start_time')[:20]
        
        shifts_data = []
        for shift in shifts:
            shifts_data.append({
                'id': shift.id,
                'start_time': timezone.localtime(shift.start_time).strftime('%d.%m.%Y %H:%M:%S'),
                'end_time': timezone.localtime(shift.end_time).strftime('%d.%m.%Y %H:%M:%S') if shift.end_time else 'Активна',
                'operator': shift.operator.get_full_name(),
                'duration': shift.get_duration_display(),
                'total_pulses': shift.total_pulses,
                'total_meters': float(shift.total_meters),
                'status': shift.get_status_display(),
            })
        
        return JsonResponse({'success': True, 'shifts': shifts_data})
        
    except Exception as e:
        logger.error(f"Error in shifts_history_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)