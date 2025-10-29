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
        
        logger.info(f"✅ Shift started: {operator.get_full_name()} on {machine.name}")
        
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
        logger.error(f"❌ Error in shift_start_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def shift_end_api(request):
    """API для окончания смены"""
    from django.db import transaction
    
    try:
        data = json.loads(request.body)
        esp32_id = data.get('esp32_id')
        rfid_uid = data.get('rfid_uid')
        
        logger.info(f"Shift end request: esp32_id={esp32_id}, rfid_uid='{rfid_uid}'")
        
        # Используем транзакцию для атомарности
        with transaction.atomic():
            # Находим станок (с блокировкой строки)
            machine = Machine.objects.select_for_update().get(esp32_id=esp32_id, is_active=True)
            
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
            
            # КРИТИЧНО: Завершаем смену на станке и обнуляем счетчики
            logger.info(f"🔄 До обнуления - meters: {machine.current_meters}, pulses: {machine.current_pulse_count}")
            
            # НЕ вызываем end_shift() - делаем все вручную!
            # Обнуляем ВСЕ поля ОДНОВРЕМЕННО
            machine.status = 'idle'
            machine.current_operator = None
            machine.current_pulse_count = 0  # ← Обнуляем импульсы (meters пересчитается автоматически)
            
            # ОДИН вызов save() для всех полей
            machine.save()
            
            logger.info(f"✅ После save() - meters: {machine.current_meters}, pulses: {machine.current_pulse_count}")
        
        # КРИТИЧНО: Перечитываем из БД ПОСЛЕ транзакции
        machine.refresh_from_db()
        logger.info(f"✅ После refresh - meters: {machine.current_meters}, pulses: {machine.current_pulse_count}, operator: {machine.current_operator}")
        
        return JsonResponse({
            'success': True,
            'message': f'Смена завершена: {operator.get_full_name()}',
            'shift': {
                'total_pulses': active_shift.total_pulses if active_shift else 0,
                'total_meters': float(active_shift.total_meters) if active_shift else 0,
                'duration_hours': active_shift.duration_hours if active_shift else 0
            }
        })
        
    except Machine.DoesNotExist:
        logger.error(f"❌ Machine not found with ESP32 ID: {esp32_id}")
        return JsonResponse({'error': 'Станок не найден'}, status=404)
    except Exception as e:
        logger.error(f"❌ Error in shift_end_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def pulse_update_api(request):
    """API для обновления счетчика импульсов (ОПТИМИЗИРОВАНО для высоких скоростей)"""
    from django.db import transaction
    
    try:
        data = json.loads(request.body)
        esp32_id = data.get('esp32_id')
        pulse_count = data.get('pulse_count', 0)
        
        # Валидация входных данных
        if not esp32_id or pulse_count <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Некорректные данные'
            }, status=400)
        
        # КРИТИЧНО: Используем транзакцию для атомарности при высоких частотах
        with transaction.atomic():
            # Находим станок с блокировкой строки
            machine = Machine.objects.select_for_update().get(
                esp32_id=esp32_id, 
                is_active=True
            )
            
            # Проверяем, что станок работает
            if not machine.current_operator:
                return JsonResponse({
                    'success': False,
                    'error': 'Станок не работает - нет оператора'
                }, status=400)
            
            # Логируем до обновления (для отладки высоких скоростей)
            old_pulses = machine.current_pulse_count
            old_meters = machine.current_meters
            
            # АТОМАРНОЕ обновление счетчика импульсов
            machine.current_pulse_count += pulse_count
            machine.save(update_fields=['current_pulse_count'])
            
            # Находим активную смену (с блокировкой)
            active_shift = Shift.objects.select_for_update().filter(
                machine=machine, 
                operator=machine.current_operator, 
                status='active'
            ).first()
            
            if active_shift:
                # БЫСТРОЕ создание лога импульсов (без лишних полей)
                PulseLog.objects.create(
                    machine=machine,
                    shift=active_shift,
                    timestamp=timezone.now(),
                    pulse_count=pulse_count,
                    total_pulses=machine.current_pulse_count,
                    meters_produced=machine.current_meters
                )
                
                # АТОМАРНОЕ обновление смены
                active_shift.total_pulses = machine.current_pulse_count
                active_shift.total_meters = machine.current_meters
                active_shift.save(update_fields=['total_pulses', 'total_meters'])
        
        # Перечитываем из БД ПОСЛЕ транзакции для точного current_meters
        machine.refresh_from_db()
        
        # Логирование для высокоскоростной отладки
        logger.info(f"⚡ HIGH-SPEED: +{pulse_count} импульсов | "
                   f"Всего: {old_pulses}→{machine.current_pulse_count} | "
                   f"Метраж: {old_meters:.6f}→{machine.current_meters:.6f}м")
        
        
        return JsonResponse({
            'success': True,
            'total_pulses': machine.current_pulse_count,
            'total_meters': float(machine.current_meters),
            'pulse_rate': f"{pulse_count} pulses/30s",
            'meters_per_pulse': float(machine.meters_per_pulse)
        })
        
    except Machine.DoesNotExist:
        logger.error(f"❌ Станок не найден: ESP32_ID={esp32_id}")
        return JsonResponse({
            'success': False,
            'error': f'Станок {esp32_id} не найден'
        }, status=404)
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ошибка в pulse_update_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }, status=500)

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
        
        # Получаем все активные станки
        machines = Machine.objects.filter(is_active=True).order_by('id')
        
        # Для каждого станка получаем активный вызов мастера
        machines_data = []
        for machine in machines:
            active_call = MaintenanceCall.objects.filter(
                machine=machine, 
                status__in=['pending', 'in_progress']
            ).select_related('master').first()
            
            machines_data.append({
                'machine': machine,
                'active_call': active_call,
            })
        
        context['machines_data'] = machines_data
        
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


class MachineDetailView(TemplateView):
    """Детальная страница станка"""
    template_name = 'lohia_monitor/machine_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        machine_id = kwargs.get('machine_id')
        machine = get_object_or_404(Machine, id=machine_id)
        
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
        
        # Последние импульсы (для графика)
        recent_pulses = PulseLog.objects.filter(
            machine=machine
        ).order_by('-timestamp')[:20]
        
        # Последние 5 смен
        recent_shifts = Shift.objects.filter(
            machine=machine
        ).select_related('operator').order_by('-start_time')[:5]
        
        # Последние 5 вызовов мастера
        recent_calls = MaintenanceCall.objects.filter(
            machine=machine
        ).select_related('operator', 'master').order_by('-call_time')[:5]
        
        context.update({
            'machine': machine,
            'active_shift': active_shift,
            'active_call': active_call,
            'recent_pulses': recent_pulses,
            'recent_shifts': recent_shifts,
            'recent_calls': recent_calls,
        })
        
        return context


# ===== Страница мастера =====
def master_page(request):
    return render(request, 'lohia_monitor/master.html')

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
        # Получаем последние 50 вызовов (можно настроить)
        calls = MaintenanceCall.objects.select_related(
            'operator', 'master', 'machine'
        ).order_by('-call_time')[:50]
        
        calls_data = []
        for call in calls:
            # Форматируем время реакции
            response_time_display = '—'
            if call.response_time:
                total_seconds = int(call.response_time.total_seconds())
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                if minutes > 0:
                    response_time_display = f"{minutes} мин {seconds} сек"
                else:
                    response_time_display = f"{seconds} сек"
            
            # Форматируем время ремонта
            repair_time_display = '—'
            if call.repair_time:
                total_seconds = int(call.repair_time.total_seconds())
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                if minutes > 0:
                    repair_time_display = f"{minutes} мин {seconds} сек"
                else:
                    repair_time_display = f"{seconds} сек"
            
            calls_data.append({
                'id': call.id,
                'date': timezone.localtime(call.call_time).strftime('%d.%m.%Y'),
                'call_time': timezone.localtime(call.call_time).strftime('%H:%M'),
                'machine': call.machine.name if call.machine else 'Неизвестно',
                'operator': call.operator.get_full_name() if call.operator else 'Неизвестно',
                'master': call.master.get_full_name() if call.master else None,
                'status': call.status,
                'status_display': call.get_status_display(),
                'response_time': response_time_display,
                'repair_time': repair_time_display,
                'description': call.description if call.description else None,
            })
        
        return JsonResponse({
            'success': True,
            'calls': calls_data,
            'count': len(calls_data)
        })
        
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

@require_http_methods(["GET"])
def machine_detail_api(request, machine_id):
    """API для получения данных конкретной машины"""
    try:
        machine = get_object_or_404(Machine, id=machine_id)
        
        # Последние 5 смен
        recent_shifts = Shift.objects.filter(
            machine=machine
        ).select_related('operator').order_by('-start_time')[:5]
        
        # Последние 5 вызовов
        recent_calls = MaintenanceCall.objects.filter(
            machine=machine
        ).select_related('operator', 'master').order_by('-call_time')[:5]
        
        shifts_data = []
        for shift in recent_shifts:
            shifts_data.append({
                'operator': shift.operator.get_full_name(),
                'start_time': timezone.localtime(shift.start_time).strftime('%d.%m %H:%M'),
                'end_time': timezone.localtime(shift.end_time).strftime('%d.%m %H:%M') if shift.end_time else None,
                'duration': shift.get_duration_display(),
                'total_meters': float(shift.total_meters),
                'status': shift.status,
            })
        
        calls_data = []
        for call in recent_calls:
            calls_data.append({
                'call_time': timezone.localtime(call.call_time).strftime('%d.%m %H:%M'),
                'operator': call.operator.get_full_name(),
                'master': call.master.get_full_name() if call.master else None,
                'response_time': call.get_response_time_display(),
                'repair_time': call.get_repair_time_display(),
                'status': call.status,
            })
        
        return JsonResponse({
            'success': True,
            'shifts': shifts_data,
            'calls': calls_data,
        })
        
    except Exception as e:
        logger.error(f"Error in machine_detail_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def dashboard_status_all_api(request):
    """API для получения статуса всех станков (для упрощенного dashboard)"""
    try:
        machines = Machine.objects.filter(is_active=True).order_by('id')
        
        machines_data = []
        for machine in machines:
            # Активный вызов мастера
            active_call = MaintenanceCall.objects.filter(
                machine=machine, 
                status__in=['pending', 'in_progress']
            ).select_related('master').first()
            
            machine_data = {
                'machine_id': machine.id,
                'name': machine.name,
                'status': machine.status,
                'current_operator': machine.current_operator.get_full_name() if machine.current_operator else None,
                'current_meters': float(machine.current_meters),
                'current_pulse_count': machine.current_pulse_count,
                'call_status': active_call.status if active_call else None,
                'master': active_call.master.get_full_name() if active_call and active_call.master else None,
            }
            
            machines_data.append(machine_data)
        
        logger.debug(f"Dashboard API: returning {len(machines_data)} machines")
        
        return JsonResponse({
            'success': True,
            'machines': machines_data
        })
        
    except Exception as e:
        logger.error(f"Error in dashboard_status_all_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def machine_stats_api(request):
    """API для обновления статистики станка (AJAX)"""
    try:
        machine = Machine.objects.filter(is_active=True).first()
        
        if not machine:
            return JsonResponse({'success': False, 'error': 'Станок не найден'}, status=404)
        
        # Общая статистика
        total_shifts = Shift.objects.filter(machine=machine).count()
        total_meters = Shift.objects.filter(machine=machine).aggregate(
            total=models.Sum('total_meters')
        )['total'] or 0
        
        total_calls = MaintenanceCall.objects.filter(machine=machine).count()
        
        # Среднее время реакции
        completed_calls = MaintenanceCall.objects.filter(
            machine=machine, 
            start_time__isnull=False
        )
        
        avg_response_time = 0
        if completed_calls.exists():
            total_response_seconds = 0
            count = 0
            for call in completed_calls:
                if call.response_time:
                    total_response_seconds += call.response_time.total_seconds()
                    count += 1
            
            avg_response_time = total_response_seconds / count / 60 if count > 0 else 0
        
        # Производительность
        avg_meters_per_shift = float(total_meters) / total_shifts if total_shifts > 0 else 0
        calls_per_shift = total_calls / total_shifts if total_shifts > 0 else 0
        
        return JsonResponse({
            'success': True,
            'total_shifts': total_shifts,
            'total_meters': float(total_meters),
            'total_calls': total_calls,
            'avg_response_time': round(avg_response_time, 1),
            'avg_meters_per_shift': round(avg_meters_per_shift, 0),
            'calls_per_shift': round(calls_per_shift, 2),
            'current_operator': machine.current_operator.get_full_name() if machine.current_operator else None,
            'current_pulse_count': machine.current_pulse_count,
            'current_meters': float(machine.current_meters),
            'status': machine.status,
        })
        
    except Exception as e:
        logger.error(f"Error in machine_stats_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ===== AJAX POLLING API ENDPOINTS =====

@login_required
def machines_polling_api(request):
    """
    API для AJAX polling - получение статуса всех станков.
    Возвращает данные для обновления дашборда Lohia.
    """
    try:
        machines = Machine.objects.filter(is_active=True).select_related('current_operator')
        
        data = []
        for machine in machines:
            # Получаем активную смену если есть
            active_shift = None
            if machine.current_operator:
                active_shift = Shift.objects.filter(
                    machine=machine,
                    operator=machine.current_operator,
                    status='active'
                ).first()
            
            # Получаем активный вызов мастера
            active_call = MaintenanceCall.objects.filter(
                machine=machine,
                status='pending'
            ).first()
            
            data.append({
                'id': machine.id,
                'name': machine.name,
                'esp32_id': machine.esp32_id,
                'status': machine.status,
                'status_display': machine.get_status_display(),
                'current_meters': float(machine.current_meters),
                'current_pulse_count': machine.current_pulse_count,
                'meters_per_pulse': float(machine.meters_per_pulse),
                'current_operator': {
                    'id': machine.current_operator.id,
                    'name': machine.current_operator.get_full_name(),
                } if machine.current_operator else None,
                'shift': {
                    'id': active_shift.id,
                    'start_time': active_shift.start_time.isoformat(),
                    'total_pulses': active_shift.total_pulses,
                    'total_meters': float(active_shift.total_meters),
                } if active_shift else None,
                'maintenance_call': {
                    'id': active_call.id,
                    'call_time': active_call.call_time.isoformat(),
                    'status': active_call.status,
                } if active_call else None,
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in machines_polling_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)