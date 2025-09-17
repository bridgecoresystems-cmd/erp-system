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
from datetime import datetime, date, timedelta

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
                f'{entry.hours_worked:.2f}' if entry.hours_worked else '',
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
                'hours_worked': float(entry.hours_worked) if entry.hours_worked else 0,
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
def worktime_entry_update(request, entry_id):
    """AJAX обновление записи рабочего времени"""
    try:
        entry = get_object_or_404(WorkTimeEntry, id=entry_id)
        
        # Получаем данные из POST запроса
        import json
        data = json.loads(request.body)
        
        # Обновляем поля
        if 'entry_time' in data and data['entry_time']:
            entry.entry_time = datetime.strptime(data['entry_time'], '%H:%M').time()
        
        if 'exit_time' in data and data['exit_time']:
            entry.exit_time = datetime.strptime(data['exit_time'], '%H:%M').time()
        
        if 'notes' in data:
            entry.notes = data['notes']
        
        # Отмечаем как скорректированное HR
        entry.is_corrected = True
        entry.created_by = request.user
        
        entry.save()  # Часы пересчитаются автоматически
        
        return JsonResponse({
            'success': True,
            'message': f'Запись для {entry.employee.get_full_name()} обновлена',
            'entry': {
                'hours_worked': float(entry.hours_worked) if entry.hours_worked else 0,
                'status': entry.get_status_display(),
                'status_color': entry.get_status_display_color()
            }
        })
        
    except WorkTimeEntry.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Запись не найдена'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при обновлении: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def worktime_entry_create(request):
    """AJAX создание новой записи рабочего времени"""
    try:
        import json
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
        # Перенаправление для HR пользователей
        if request.user.is_authenticated:
            if request.user.groups.filter(name='HR_Admins').exists():
                return redirect('employees:employee_list')
            elif request.user.groups.filter(name='HR_Users').exists():
                return redirect('employees:worktime_list')
            elif request.user.groups.filter(name='Security_Users').exists():
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
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(position__icontains=search_query) |
                Q(department__icontains=search_query) |
                Q(employee_id__icontains=search_query)
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
    API endpoint для ESP32
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
                    'timestamp': access.timestamp.strftime('%d.%m.%Y %H:%M:%S'),
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
    today = datetime.now().date()
    
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
        'last_update': datetime.now().strftime('%H:%M:%S')
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
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        
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