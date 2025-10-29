# employees/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

import json
import logging
import csv
from datetime import datetime, date, timedelta, time
from django.utils import timezone
from .models import Employee, CardAccess, WorkTimeEntry
from .forms import EmployeeForm

logger = logging.getLogger(__name__)

class WorkTimeListView(LoginRequiredMixin, ListView):
    """Список записей рабочего времени с фильтрацией"""
    model = WorkTimeEntry
    template_name = 'employees/worktime_list.html'
    context_object_name = 'worktime_entries'
    paginate_by = 20
    ordering = ['-date', 'employee__last_name']
    
    def get_queryset(self):
        queryset = WorkTimeEntry.objects.select_related('employee').filter(
            employee__is_active=True
        )
        
        # Фильтрация по сотруднику
        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Фильтрация по датам
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Фильтрация по отделу
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(employee__department=department)
        
        # Фильтрация по статусу
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Для отображения выбранного сотрудника в фильтре
        employee_id = self.request.GET.get('employee')
        if employee_id:
            try:
                context['selected_employee'] = Employee.objects.get(id=employee_id, is_active=True)
            except Employee.DoesNotExist:
                pass
            
        # Список отделов для фильтра
        context['departments'] = Employee.objects.filter(is_active=True).values_list('department', flat=True).distinct().order_by('department')
        
        # Статистика по текущей выборке
        queryset = self.get_queryset()
        context['stats'] = {
            'total_entries': queryset.count(),
            'total_hours': queryset.aggregate(total=Sum('hours_worked'))['total'] or 0,
            'late_count': queryset.filter(status='late').count(),
            'overtime_hours': sum(entry.get_overtime_hours() for entry in queryset if entry.hours_worked)
        }
        
        return context
    
    def get(self, request, *args, **kwargs):
        # Проверяем запрос на экспорт
        if request.GET.get('export') == 'csv':
            return self.export_csv()
        
        return super().get(request, *args, **kwargs)
    
    def export_csv(self):
        """Экспорт данных в CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="worktime_report_{datetime.now().strftime("%Y%m%d")}.csv"'
        response.write('\ufeff')  # BOM для корректного отображения в Excel
        
        writer = csv.writer(response)
        writer.writerow([
            'Дата', 'ФИО', 'Табельный номер', 'Отдел', 
            'Приход', 'Уход', 'Часы', 'Статус', 'Примечания'
        ])
        
        for entry in self.get_queryset():
            writer.writerow([
                entry.date.strftime('%d.%m.%Y'),
                entry.employee.get_full_name(),
                entry.employee.employee_id,
                entry.employee.department,
                entry.entry_time.strftime('%H:%M') if entry.entry_time else '',
                entry.exit_time.strftime('%H:%M') if entry.exit_time else '',
                entry.get_hours_display() if entry.hours_worked else '00:00',
                entry.get_status_display(),
                entry.notes or ''
            ])
        
        return response


@login_required
@require_http_methods(["POST"])
def worktime_entry_delete(request, entry_id):
    """AJAX удаление записи рабочего времени"""
    try:
        entry = get_object_or_404(WorkTimeEntry, id=entry_id)
        employee_name = entry.employee.get_full_name()
        entry_date = entry.date
        
        entry.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Запись для {employee_name} от {entry_date.strftime("%d.%m.%Y")} удалена'
        })
        
    except WorkTimeEntry.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Запись не найдена'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при удалении: {str(e)}'
        }, status=500)


@login_required
def worktime_entry_detail(request, entry_id):
    """API для получения детальной информации о записи"""
    try:
        entry = get_object_or_404(WorkTimeEntry, id=entry_id)
        
        return JsonResponse({
            'success': True,
            'entry': {
                'id': entry.id,
                'employee_id': entry.employee.id,
                'employee_name': entry.employee.get_full_name(),
                'date': entry.date.strftime('%Y-%m-%d'),
                'entry_time': entry.entry_time.strftime('%H:%M') if entry.entry_time else '',
                'exit_time': entry.exit_time.strftime('%H:%M') if entry.exit_time else '',
                'hours_worked': entry.get_hours_display() if entry.hours_worked else '00:00',
                'status': entry.status,
                'notes': entry.notes or '',
                'is_manual_entry': entry.is_manual_entry,
                'is_corrected': entry.is_corrected
            }
        })
        
    except WorkTimeEntry.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Запись не найдена'
        }, status=404)

@login_required
@require_http_methods(["POST"])
def worktime_entry_create(request):
    """AJAX создание новой записи рабочего времени"""
    try:
        data = json.loads(request.body)
        
        employee = get_object_or_404(Employee, id=data['employee_id'])
        entry_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Проверяем что запись за эту дату не существует
        if WorkTimeEntry.objects.filter(employee=employee, date=entry_date).exists():
            return JsonResponse({
                'success': False,
                'error': f'Запись для {employee.get_full_name()} за {entry_date.strftime("%d.%m.%Y")} уже существует'
            }, status=400)
        
        # Создаем новую запись
        entry = WorkTimeEntry.objects.create(
            employee=employee,
            date=entry_date,
            entry_time=datetime.strptime(data['entry_time'], '%H:%M').time() if data.get('entry_time') else None,
            exit_time=datetime.strptime(data['exit_time'], '%H:%M').time() if data.get('exit_time') else None,
            notes=data.get('notes', ''),
            is_manual_entry=True,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Запись для {employee.get_full_name()} создана',
            'entry_id': entry.id
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Сотрудник не найден'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при создании записи: {str(e)}'
        }, status=500)
    
@login_required
@require_http_methods(["POST"])
def worktime_entry_update(request, entry_id):
    """AJAX обновление записи рабочего времени"""
    try:
        entry = get_object_or_404(WorkTimeEntry, id=entry_id)
        
        # Получаем данные из POST запроса
        data = json.loads(request.body)
        
        # Обновляем только время, НЕ трогаем employee и date
        if 'entry_time' in data and data['entry_time']:
            entry.entry_time = datetime.strptime(data['entry_time'], '%H:%M').time()
        elif 'entry_time' in data and not data['entry_time']:
            entry.entry_time = None
        
        if 'exit_time' in data and data['exit_time']:
            entry.exit_time = datetime.strptime(data['exit_time'], '%H:%M').time()
        elif 'exit_time' in data and not data['exit_time']:
            entry.exit_time = None
        
        if 'notes' in data:
            entry.notes = data['notes']
        
        # Отмечаем как скорректированное HR
        entry.is_corrected = True
        entry.created_by = request.user
        
        entry.save()  # Часы пересчитаются автоматически
        
        return JsonResponse({
            'success': True,
            'message': f'Запись для {entry.employee.get_full_name()} обновлена'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при обновлении: {str(e)}'
        }, status=500)
    

def worktime_stats_api(request):
    """API для получения статистики рабочего времени"""
    try:
        # Параметры для фильтрации
        employee_id = request.GET.get('employee_id')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to', date.today().strftime('%Y-%m-%d'))
        
        # Базовый queryset
        queryset = WorkTimeEntry.objects.select_related('employee')
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        queryset = queryset.filter(date__lte=date_to)
        
        # Статистика
        stats = {
            'total_days': queryset.count(),
            'working_days': queryset.filter(status='present').count(),
            'late_days': queryset.filter(status='late').count(),
            'partial_days': queryset.filter(status='partial').count(),
            'total_hours': float(queryset.aggregate(total=Sum('hours_worked'))['total'] or 0),
            'average_hours': 0,
            'overtime_hours': 0
        }
        
        # Расчет средних часов и сверхурочных
        if stats['total_days'] > 0:
            stats['average_hours'] = round(stats['total_hours'] / stats['total_days'], 2)
        
        # Сверхурочные часы
        for entry in queryset:
            if entry.hours_worked and entry.hours_worked > 8:
                stats['overtime_hours'] += entry.hours_worked - 8
        
        stats['overtime_hours'] = round(stats['overtime_hours'], 2)
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка получения статистики: {str(e)}'
        }, status=500)


class HomeView(TemplateView):
    template_name = 'employees/home.html'
    
    def get(self, request, *args, **kwargs):
        # Перенаправление для пользователей с группами
        if request.user.is_authenticated:
            user_groups = [g.name for g in request.user.groups.all()]
            
            if 'HR_Admins' in user_groups:
                return redirect('employees:employee_list')
            elif 'HR_Users' in user_groups:
                return redirect('employees:worktime_list')
            elif 'Security' in user_groups:
                return redirect('security:dashboard')
            elif 'Security_Users' in user_groups:
                return redirect('employees:security_display')
        
        return super().get(request, *args, **kwargs)


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    """Добавление нового сотрудника"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Сотрудник {form.instance.get_full_name()} успешно добавлен!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавить сотрудника'
        context['submit_text'] = 'Добавить сотрудника'
        return context

class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование сотрудника"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Данные сотрудника {form.instance.get_full_name()} успешно обновлены!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактировать: {self.object.get_full_name()}'
        context['submit_text'] = 'Сохранить изменения'
        return context

class EmployeeDeleteView(DeleteView):
    """Удаление сотрудника"""
    model = Employee
    success_url = reverse_lazy('employees:employee_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        employee_name = self.object.get_full_name()
        
        # Деактивируем сотрудника вместо физического удаления
        self.object.is_active = False
        self.object.save()
        
        messages.success(request, f'Сотрудник {employee_name} успешно удален из системы!')
        return JsonResponse({
            'success': True, 
            'message': f'Сотрудник {employee_name} удален',
            'redirect_url': str(self.success_url)
        })

@login_required
def employee_delete_ajax(request, pk):
    """AJAX удаление сотрудника"""
    if request.method == 'POST':
        try:
            employee = get_object_or_404(Employee, pk=pk)
            employee_name = employee.get_full_name()
            
            # Проверяем есть ли связанные записи доступа
            access_count = CardAccess.objects.filter(employee=employee).count()
            
            # Деактивируем вместо удаления
            employee.is_active = False
            employee.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Сотрудник {employee_name} успешно удален из системы!',
                'access_records': access_count
            })
            
        except Employee.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Сотрудник не найден'
            }, status=404)
        except Exception as e:
            logger.error(f"Error deleting employee: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Ошибка при удалении: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'}, status=405)

# НОВЫЙ VIEW - Список сотрудников
class EmployeeListView(LoginRequiredMixin, ListView):
    """Список всех сотрудников с пагинацией и поиском"""
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20
    ordering = ['last_name', 'first_name']
    
    def get_queryset(self):
        queryset = Employee.objects.filter(is_active=True)
        
        # Поиск по имени/фамилии/должности/цеху
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            # Разбиваем поисковый запрос на слова
            search_words = search_query.split()
            
            if len(search_words) == 1:
                # Один поисковый термин - ищем по всем полям
                queryset = queryset.filter(
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query) |
                    Q(middle_name__icontains=search_query) |
                    Q(position__icontains=search_query) |
                    Q(department__icontains=search_query) |
                    Q(employee_id__icontains=search_query)
                )
            else:
                # Несколько слов - умный поиск по ФИО
                # Применяем фильтр для каждого слова (все слова должны присутствовать)
                for word in search_words:
                    queryset = queryset.filter(
                        Q(first_name__icontains=word) |
                        Q(last_name__icontains=word) |
                        Q(middle_name__icontains=word) |
                        Q(position__icontains=word) |
                        Q(department__icontains=word) |
                        Q(employee_id__icontains=word)
                    )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['total_employees'] = Employee.objects.filter(is_active=True).count()
        return context


# API для ESP32 (оставляем как есть)
@csrf_exempt
@require_http_methods(["POST"])
def rfid_scan(request):
    """
    API endpoint для ESP32 - универсальный для всех модулей
    POST /api/rfid-scan/
    {
        "rfid_uid": "04A1B2C3",
        "device_id": "ESP32-001"
    }
    """
    # Логируем входящий запрос
    logger.info(f"RFID scan request received from {request.META.get('REMOTE_ADDR')}")
    logger.info(f"Request body: {request.body}")
    
    try:
        data = json.loads(request.body)
        rfid_uid = data.get('rfid_uid', '').strip().upper()  # Приводим к верхнему регистру
        device_id = data.get('device_id', 'ESP32-001')
        
        logger.info(f"Parsed data - RFID: {rfid_uid}, Device: {device_id}")
        
        if not rfid_uid:
            logger.warning("Empty RFID UID received")
            return JsonResponse({
                'success': False,
                'error': 'RFID UID не предоставлен'
            }, status=400)
        
        # Поиск сотрудника по RFID
        try:
            # Также приводим к верхнему регистру для поиска
            employee = Employee.objects.get(rfid_uid__iexact=rfid_uid, is_active=True)
            
            logger.info(f"Employee found: {employee.get_full_name()} (ID: {employee.id})")
            
            # Логируем касание
            access_log = CardAccess.objects.create(
                employee=employee,
                rfid_uid=rfid_uid,
                device_id=device_id,
                success=True
            )
            
            
            # Проверяем, это устройство lohia_monitor?
            if device_id.startswith('LOHIA-'):
                # Логика для lohia_monitor
                return handle_lohia_rfid(employee, device_id, rfid_uid)
            
            # Обычная логика для employees (контроль доступа)
            # Создаем или обновляем запись рабочего времени
            today = date.today()
            work_entry, created = WorkTimeEntry.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={
                    'entry_time': timezone.localtime(timezone.now()).time(),
                    'is_manual_entry': False,
                    'status': 'present'
                }
            )

            # Логика входа/выхода
            if created:
                # Новая запись - это вход
                action = 'entry'
                work_entry.entry_time = timezone.localtime(timezone.now()).time()
            elif work_entry.exit_time is None:
                # Запись существует, но нет времени выхода - это выход
                action = 'exit'
                work_entry.exit_time = timezone.localtime(timezone.now()).time()
            else:
                # Уже есть и вход и выход - создаем новую запись для повторного входа
                work_entry = WorkTimeEntry.objects.create(
                    employee=employee,
                    date=today,
                    entry_time=timezone.localtime(timezone.now()).time(),
                    is_manual_entry=False,
                    status='present'
                )
                action = 'entry'

            work_entry.save()  # Статус обновится автоматически
            
            logger.info(f"WorkTime {action} recorded for {employee.get_full_name()}")
            
            logger.info(f"Access logged with ID: {access_log.id}")
            
            # Возвращаем данные сотрудника
            response_data = {
                'success': True,
                'employee': {
                    'id': employee.id,
                    'full_name': employee.get_full_name(),
                    'first_name': employee.first_name,
                    'last_name': employee.last_name,
                    'department': employee.department,
                    'position': employee.position,
                    'employee_id': employee.employee_id,
                    'photo_url': employee.get_photo_url(),
                },
                'message': f'Добро пожаловать, {employee.get_full_name()}!'
            }
            
            logger.info(f"Sending success response: {response_data}")
            return JsonResponse(response_data)
            
        except Employee.DoesNotExist:
            logger.warning(f"Employee not found for RFID: {rfid_uid}")
            
            # Логируем неудачное касание
            CardAccess.objects.create(
                employee=None,
                rfid_uid=rfid_uid,
                device_id=device_id,
                success=False
            )
            
            response_data = {
                'success': False,
                'error': 'Карта не найдена или заблокирована',
                'rfid_uid': rfid_uid
            }
            
            logger.info(f"Sending not found response: {response_data}")
            return JsonResponse(response_data, status=404)
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат JSON'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Unexpected error in rfid_scan: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }, status=500)


def handle_lohia_rfid(employee, device_id, rfid_uid):
    """Обработка RFID для lohia_monitor"""
    try:
        from lohia_monitor.models import Machine, Shift, MaintenanceCall
        
        # Находим станок по device_id
        try:
            machine = Machine.objects.get(esp32_id=device_id, is_active=True)
        except Machine.DoesNotExist:
            return JsonResponse({'error': 'Station not found'}, status=404)
        
        # Логика в зависимости от роли сотрудника
        if employee.department in ['Сотрудник_bag', 'Операторы', 'Сотрудник', 'Администрация']:
            # Оператор - начало/окончание смены
            # Проверяем активную смену на этом станке
            active_shift = Shift.objects.filter(
                machine=machine, 
                status='active'
            ).first()
            
            if active_shift and active_shift.operator == employee:
                # У этого оператора есть активная смена - завершаем её
                active_shift.total_pulses = machine.current_pulse_count
                active_shift.total_meters = machine.current_meters
                active_shift.complete_shift()
                
                # КРИТИЧНО: Обнуляем счетчики ЗДЕСЬ!
                logger.info(f"🔄 До обнуления - pulses: {machine.current_pulse_count}, meters: {machine.current_meters}")
                
                machine.status = 'idle'
                machine.current_operator = None
                machine.current_pulse_count = 0  # ← Обнуляем импульсы!
                machine.save()
                
                logger.info(f"✅ После обнуления - pulses: {machine.current_pulse_count}, meters: {machine.current_meters}")
                
                # Отправляем WebSocket
                from lohia_monitor.views import send_websocket_update
                send_websocket_update(machine)
                
                action = 'shift_ended'
                message = f'Смена завершена, {employee.get_full_name()}'
            elif active_shift and active_shift.operator != employee:
                # На станке работает другой оператор - завершаем его смену и начинаем свою
                active_shift.total_pulses = machine.current_pulse_count
                active_shift.total_meters = machine.current_meters
                active_shift.complete_shift()
                logger.info(f"Completed other operator's shift: {active_shift.operator.get_full_name()}")
                
                # Обнуляем счетчики перед новой сменой
                machine.current_pulse_count = 0
                
                # Начинаем новую смену для текущего оператора
                machine.start_shift(employee)
                shift = Shift.objects.create(
                    operator=employee,
                    machine=machine,
                    start_time=timezone.now()
                )
                
                # Отправляем WebSocket
                from lohia_monitor.views import send_websocket_update
                send_websocket_update(machine)
                
                action = 'shift_started'
                message = f'Смена начата, {employee.get_full_name()}'
            else:
                # На станке нет активной смены - начинаем новую
                machine.start_shift(employee)  # ← Обнуляет импульсы внутри
                shift = Shift.objects.create(
                    operator=employee,
                    machine=machine,
                    start_time=timezone.now()
                )
                
                # Отправляем WebSocket
                from lohia_monitor.views import send_websocket_update
                send_websocket_update(machine)
                
                action = 'shift_started'
                message = f'Смена начата, {employee.get_full_name()}'
                
        elif employee.department == 'Механики':
            # Мастер - принимаем/решаем активные вызовы
            active_call = MaintenanceCall.objects.filter(
                machine=machine, 
                status='pending'
            ).first()
            
            if active_call:
                # Начинаем ремонт
                active_call.start_maintenance(employee)
                
                # Отправляем WebSocket
                from lohia_monitor.views import send_websocket_update
                send_websocket_update(machine)
                
                action = 'maintenance_started'
                message = f'Ремонт начат мастером {employee.get_full_name()}'
            else:
                # Проверяем, есть ли активный ремонт
                in_progress_call = MaintenanceCall.objects.filter(
                    machine=machine, 
                    status='in_progress',
                    master=employee
                ).first()
                
                if in_progress_call:
                    # Завершаем ремонт
                    in_progress_call.complete_maintenance('Ремонт завершен')
                    
                    # Отправляем WebSocket
                    from lohia_monitor.views import send_websocket_update
                    send_websocket_update(machine)
                    
                    action = 'maintenance_completed'
                    message = f'Ремонт завершен мастером {employee.get_full_name()}'
                else:
                    action = 'no_maintenance'
                    message = f'Нет активных вызовов для {employee.get_full_name()}'
        else:
            # Начальник цеха или другие - информационное сообщение
            action = 'info_only'
            message = f'Информация: {employee.get_full_name()} - {employee.department}'
        
        # Отправляем WebSocket уведомление для lohia dashboard
        from lohia_monitor.views import send_websocket_update
        send_websocket_update(machine)
        
        return JsonResponse({
            'success': True,
            'action': action,
            'message': message,
            'employee': {
                'name': employee.get_full_name(),
                'department': employee.department,
            },
            'machine': {
                'name': machine.name,
                'status': machine.status,
                'current_operator': machine.current_operator.get_full_name() if machine.current_operator else None,
            }
        })
        
    except Exception as e:
        logger.error(f"Error in lohia RFID handling: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)




class SecurityDisplayView(TemplateView):
    """Экран для охраны - показывает информацию о сотруднике"""
    template_name = 'employees/security_display.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем последнее касание карты
        latest_access = CardAccess.objects.filter(success=True).select_related('employee').first()
        
        context['latest_access'] = latest_access
        context['total_employees'] = Employee.objects.filter(is_active=True).count()
        
        return context

@csrf_exempt
def worktime_latest_api(request):
    """API для получения последней записи worktime"""
    try:
        # Получаем последнюю запись
        latest_entry = WorkTimeEntry.objects.select_related('employee').order_by('-id').first()
        
        if latest_entry:
            # Проверяем, была ли запись создана в последние 10 секунд
            # Используем created_at если есть, иначе сравниваем с текущим временем
            time_diff = timezone.now() - timezone.make_aware(datetime.combine(latest_entry.date, latest_entry.entry_time or timezone.now().time()))
            is_new = time_diff.total_seconds() <= 10
            
            entry_data = {
                'id': latest_entry.id,
                'employee_name': latest_entry.employee.get_full_name(),
                'employee_id': latest_entry.employee.employee_id,
                'department': latest_entry.employee.department,
                'entry_time': latest_entry.entry_time.strftime('%H:%M') if latest_entry.entry_time else '',
                'exit_time': latest_entry.exit_time.strftime('%H:%M') if latest_entry.exit_time else '',
                'date': latest_entry.date.strftime('%d.%m.%Y'),
                'photo_url': latest_entry.employee.get_photo_url(),
                'hours_worked': latest_entry.get_hours_display() if latest_entry.hours_worked else '00:00',
                'status': latest_entry.status,
                'status_display': latest_entry.get_status_display(),
                'status_color': latest_entry.get_status_display_color(),
                'is_full_day': latest_entry.is_full_day(),
                'is_overtime': latest_entry.is_overtime(),
                'overtime_display': latest_entry.get_overtime_display() if latest_entry.is_overtime() else None,
                'is_manual_entry': latest_entry.is_manual_entry,
                'is_corrected': latest_entry.is_corrected,
            }
            
            return JsonResponse({
                'success': True,
                'has_new_entry': is_new,
                'entry_time': latest_entry.date.isoformat(),
                'entry': entry_data
            })
        else:
            return JsonResponse({
                'success': True,
                'has_new_entry': False
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def employee_detail_api(request, employee_id):
    """API для получения детальной информации о сотруднике"""
    try:
        # Исправляем: убираем is_active=True, используем pk
        employee = get_object_or_404(Employee, pk=employee_id)
        
        # Последние касания карты
        recent_accesses = CardAccess.objects.filter(
            employee=employee,
            success=True
        ).order_by('-timestamp')[:5]
        
        return JsonResponse({
            'success': True,
            'employee': {
                'id': employee.id,
                'full_name': employee.get_full_name(),
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'middle_name': employee.middle_name,
                'department': employee.department,
                'position': employee.position,
                'employee_id': employee.employee_id,
                'photo_url': employee.get_photo_url(),
                'hire_date': employee.hire_date.strftime('%d.%m.%Y'),
                'rfid_uid': employee.rfid_uid or 'Не привязана',
                'is_active': employee.is_active,
            },
            'recent_accesses': [
                {
                    'timestamp': timezone.localtime(access.timestamp).strftime('%d.%m.%Y %H:%M:%S'),
                    'device_id': access.device_id
                }
                for access in recent_accesses
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in employee_detail_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def dashboard_stats(request):
    """API для статистики на главной странице"""
    today = date.today()
    
    # Статистика за сегодня
    today_accesses = CardAccess.objects.filter(
        timestamp__date=today,
        success=True
    ).count()
    
    unique_employees_today = CardAccess.objects.filter(
        timestamp__date=today,
        success=True
    ).values('employee').distinct().count()
    
    return JsonResponse({
        'today_accesses': today_accesses,
        'unique_employees_today': unique_employees_today,
        'total_active_employees': Employee.objects.filter(is_active=True).count(),
        'last_update': timezone.localtime(timezone.now()).strftime('%H:%M:%S')
    })

@login_required
def latest_access_api(request):
    """API для получения информации о последнем касании карты"""
    try:
        # Получаем самое последнее успешное касание
        latest_access = CardAccess.objects.filter(
            success=True
        ).select_related('employee').order_by('-timestamp').first()
        
        if latest_access and latest_access.employee:
            return JsonResponse({
                'success': True,
                'has_new_access': True,
                'employee': {
                    'id': latest_access.employee.id,
                    'full_name': latest_access.employee.get_full_name(),
                    'first_name': latest_access.employee.first_name,
                    'last_name': latest_access.employee.last_name,
                    'department': latest_access.employee.department,
                    'position': latest_access.employee.position,
                    'employee_id': latest_access.employee.employee_id,
                    'photo_url': latest_access.employee.get_photo_url(),
                },
                'access_time': latest_access.timestamp.isoformat(),
                'device_id': latest_access.device_id
            })
        else:
            return JsonResponse({
                'success': True,
                'has_new_access': False,
                'message': 'Нет касаний карт'
            })
            
    except Exception as e:
        logger.error(f"Error in latest_access_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def employee_search_api(request):
    """API для поиска сотрудников по имени/фамилии"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'employees': []})
    
    # Поиск по имени и фамилии
    employees = Employee.objects.filter(
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query) |
        Q(middle_name__icontains=query),
        is_active=True
    ).order_by('last_name', 'first_name')[:10]  # Лимит 10 результатов
    
    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'full_name': emp.get_full_name(),
            'department': emp.department,
            'employee_id': emp.employee_id
        })
    
    return JsonResponse({'employees': results})

class EmployeeDetailView(LoginRequiredMixin, DetailView):
    """Детальная страница сотрудника с полной информацией"""
    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_object()
        
        # Последние касания карты (20 записей)
        context['recent_accesses'] = CardAccess.objects.filter(
            employee=employee,
            success=True
        ).order_by('-timestamp')[:20]
        
        # Записи рабочего времени за последние 30 дней
        thirty_days_ago = date.today() - timedelta(days=30)
        
        context['recent_worktime'] = WorkTimeEntry.objects.filter(
            employee=employee,
            date__gte=thirty_days_ago
        ).order_by('-date')[:15]
        
        # Статистика за последние 30 дней
        worktime_entries = WorkTimeEntry.objects.filter(
            employee=employee,
            date__gte=thirty_days_ago
        )
        
        context['stats'] = {
            'total_work_days': worktime_entries.count(),
            'present_days': worktime_entries.filter(status='present').count(),
            'late_days': worktime_entries.filter(status='late').count(),
            'partial_days': worktime_entries.filter(status='partial').count(),
            'total_hours': worktime_entries.aggregate(
                total=Sum('hours_worked')
            )['total'] or 0,
            'average_hours': 0,
            'total_accesses': CardAccess.objects.filter(
                employee=employee,
                success=True,
                timestamp__date__gte=thirty_days_ago
            ).count()
        }
        
        # Средние часы
        if context['stats']['total_work_days'] > 0:
            context['stats']['average_hours'] = round(
                context['stats']['total_hours'] / context['stats']['total_work_days'], 2
            )
        
        return context


# ===== AJAX POLLING API ENDPOINTS =====

@login_required
def worktime_polling_api(request):
    """
    API для AJAX polling - получение обновлений рабочего времени.
    Возвращает записи за сегодня для отображения на мониторе.
    """
    try:
        today = timezone.now().date()
        
        # Получаем все записи за сегодня
        entries = WorkTimeEntry.objects.filter(
            date=today
        ).select_related('employee').order_by('-entry_time')
        
        data = []
        for entry in entries:
            data.append({
                'id': entry.id,
                'employee_pk': entry.employee.id,
                'employee_id': entry.employee.employee_id,
                'employee_name': entry.employee.get_full_name(),
                'department': entry.employee.department,
                'photo_url': entry.employee.get_photo_url(),
                'date_display': entry.date.strftime('%d.%m.%Y'),
                'date_iso': entry.date.isoformat(),
                'entry_time_display': entry.entry_time.strftime('%H:%M') if entry.entry_time else '',
                'exit_time_display': entry.exit_time.strftime('%H:%M') if entry.exit_time else '',
                'hours_worked': entry.get_hours_display() if entry.hours_worked else '00:00',
                'status': entry.status,
                'status_display': entry.get_status_display(),
                'status_color': entry.get_status_display_color(),
                'is_full_day': entry.is_full_day(),
                'is_overtime': entry.is_overtime(),
                'overtime_display': entry.get_overtime_display() if entry.is_overtime() else None,
                'is_manual_entry': entry.is_manual_entry,
                'is_corrected': entry.is_corrected,
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in worktime_polling_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)