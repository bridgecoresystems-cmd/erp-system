# employees/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Employee, CardAccess, WorkTimeEntry

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'photo_thumbnail', 'get_full_name', 'employee_id', 
        'department', 'position', 'get_age_display', 'phone',
        'rfid_status', 'is_active'
    ]
    
    list_filter = [
        'department', 'position', 'is_active', 'gender', 
        'marital_status', 'hire_date'
    ]
    
    search_fields = [
        'first_name', 'last_name', 'middle_name', 'employee_id', 
        'rfid_uid', 'phone', 'email', 'inn', 'snils'
    ]
    
    list_editable = ['is_active']
    
    # Группировка полей в админке
    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'middle_name', 'photo'),
            'classes': ('wide',)
        }),
        ('Персональные данные', {
            'fields': ('birth_date', 'gender', 'marital_status'),
            'classes': ('collapse',)
        }),
        ('Контактная информация', {
            'fields': ('phone', 'email', 'address'),
            'classes': ('collapse',)
        }),
        ('Документы', {
            'fields': (
                ('passport_series', 'passport_number'),
                ('passport_issued_date', 'passport_issued_by'),
                ('inn', 'snils')
            ),
            'classes': ('collapse',)
        }),
        ('Рабочие данные', {
            'fields': ('employee_id', 'department', 'position', 'hire_date', 'is_active'),
            'classes': ('wide',)
        }),
        ('RFID доступ', {
            'fields': ('rfid_uid',),
            'classes': ('wide',)
        }),
    )
    
    # Только для чтения
    readonly_fields = ['created_at', 'updated_at']
    
    # Порядок сортировки по умолчанию
    ordering = ['last_name', 'first_name']
    
    # Количество записей на страницу
    list_per_page = 25
    
    def photo_thumbnail(self, obj):
        """Миниатюра фото для списка"""
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.photo.url
            )
        return format_html(
            '<div style="width:50px;height:50px;background:#ddd;border-radius:50%;'
            'display:flex;align-items:center;justify-content:center;font-size:20px;">👤</div>'
        )
    photo_thumbnail.short_description = 'Фото'
    
    def get_full_name(self, obj):
        """Полное имя сотрудника"""
        return obj.get_full_name()
    get_full_name.short_description = 'ФИО'
    get_full_name.admin_order_field = 'last_name'
    
    def get_age_display(self, obj):
        """Возраст сотрудника"""
        age = obj.get_age()
        if age:
            return f"{age} лет"
        return "—"
    get_age_display.short_description = 'Возраст'
    
    def rfid_status(self, obj):
        """Статус RFID карты"""
        if obj.rfid_uid:
            return format_html(
                '<span style="color: #4caf50; font-size: 16px;" title="RFID: {}">🎫</span>',
                obj.rfid_uid
            )
        return format_html(
            '<span style="color: #f44336; font-size: 16px;" title="RFID не привязан">❌</span>'
        )
    rfid_status.short_description = 'RFID'
    
    # Действия
    actions = ['activate_employees', 'deactivate_employees', 'export_to_csv']
    
    def activate_employees(self, request, queryset):
        """Массовое активирование сотрудников"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Активировано {updated} сотрудников.'
        )
    activate_employees.short_description = "Активировать выбранных сотрудников"
    
    def deactivate_employees(self, request, queryset):
        """Массовое деактивирование сотрудников"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Деактивировано {updated} сотрудников.'
        )
    deactivate_employees.short_description = "Деактивировать выбранных сотрудников"
    
    def export_to_csv(self, request, queryset):
        """Экспорт в CSV"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="employees_{datetime.now().strftime("%Y%m%d")}.csv"'
        response.write('\ufeff')  # BOM для корректного отображения в Excel
        
        writer = csv.writer(response)
        writer.writerow([
            'Табельный номер', 'Фамилия', 'Имя', 'Отчество', 
            'Отдел', 'Должность', 'Дата рождения', 'Пол',
            'Телефон', 'Email', 'Дата приема', 'RFID', 'Активен'
        ])
        
        for employee in queryset:
            writer.writerow([
                employee.employee_id,
                employee.last_name,
                employee.first_name,
                employee.middle_name or '',
                employee.department,
                employee.position,
                employee.birth_date.strftime('%d.%m.%Y') if employee.birth_date else '',
                employee.get_gender_display(),
                employee.phone or '',
                employee.email or '',
                employee.hire_date.strftime('%d.%m.%Y'),
                employee.rfid_uid or '',
                'Да' if employee.is_active else 'Нет'
            ])
        
        self.message_user(
            request,
            f'Экспортировано {queryset.count()} сотрудников в CSV.'
        )
        return response
    export_to_csv.short_description = "Экспорт в CSV"


@admin.register(CardAccess)
class CardAccessAdmin(admin.ModelAdmin):
    list_display = [
        'get_employee_name', 'timestamp', 'rfid_uid', 
        'device_id', 'success_icon', 'get_department'
    ]
    
    list_filter = [
        'success', 'device_id', 'timestamp', 
        'employee__department', 'employee__is_active'
    ]
    
    search_fields = [
        'employee__first_name', 'employee__last_name', 
        'employee__employee_id', 'rfid_uid'
    ]
    
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    # Убираем slice из get_queryset для избежания ошибки
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('employee').order_by('-timestamp')
    
    # Пагинация для лучшей производительности
    list_per_page = 100
    list_max_show_all = 500
    
    def get_employee_name(self, obj):
        """Имя сотрудника с фото"""
        if obj.employee:
            if obj.employee.photo:
                return format_html(
                    '<div style="display: flex; align-items: center; gap: 10px;">'
                    '<img src="{}" width="30" height="30" style="border-radius: 50%; object-fit: cover;" />'
                    '<span>{}</span></div>',
                    obj.employee.photo.url,
                    obj.employee.get_full_name()
                )
            else:
                return format_html(
                    '<div style="display: flex; align-items: center; gap: 10px;">'
                    '<div style="width:30px;height:30px;background:#ddd;border-radius:50%;'
                    'display:flex;align-items:center;justify-content:center;font-size:12px;">👤</div>'
                    '<span>{}</span></div>',
                    obj.employee.get_full_name()
                )
        return format_html(
            '<span style="color: #f44336;">Неизвестная карта</span>'
        )
    get_employee_name.short_description = 'Сотрудник'
    get_employee_name.admin_order_field = 'employee__last_name'
    
    def success_icon(self, obj):
        """Иконка успешности доступа"""
        if obj.success:
            return format_html(
                '<span style="color: #4caf50; font-size: 16px;" title="Доступ разрешен">✅</span>'
            )
        return format_html(
            '<span style="color: #f44336; font-size: 16px;" title="Доступ запрещен">❌</span>'
        )
    success_icon.short_description = 'Статус'
    success_icon.admin_order_field = 'success'
    
    def get_department(self, obj):
        """Отдел сотрудника"""
        if obj.employee:
            return obj.employee.department
        return "—"
    get_department.short_description = 'Отдел'
    get_department.admin_order_field = 'employee__department'
    
    # Действия
    actions = ['export_access_log']
    
    def export_access_log(self, request, queryset):
        """Экспорт журнала доступа в CSV"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="access_log_{datetime.now().strftime("%Y%m%d")}.csv"'
        response.write('\ufeff')  # BOM для корректного отображения в Excel
        
        writer = csv.writer(response)
        writer.writerow([
            'Время', 'ФИО', 'Табельный номер', 'Отдел', 
            'RFID', 'Устройство', 'Статус'
        ])
        
        for access in queryset.order_by('-timestamp'):
            writer.writerow([
                access.timestamp.strftime('%d.%m.%Y %H:%M:%S'),
                access.employee.get_full_name() if access.employee else 'Неизвестный',
                access.employee.employee_id if access.employee else '',
                access.employee.department if access.employee else '',
                access.rfid_uid,
                access.device_id,
                'Успешно' if access.success else 'Ошибка'
            ])
        
        self.message_user(
            request,
            f'Экспортировано {queryset.count()} записей доступа в CSV.'
        )
        return response
    export_access_log.short_description = "Экспорт журнала доступа"


@admin.register(WorkTimeEntry)
class WorkTimeEntryAdmin(admin.ModelAdmin):
    list_display = [
        'get_employee_name', 'date', 'entry_time', 'exit_time', 
        'get_hours_display', 'get_status_display', 'get_overtime_display'
    ]
    
    list_filter = [
        'status', 'date', 'is_manual_entry', 'is_corrected',
        'employee__department', 'employee__is_active'
    ]
    
    search_fields = [
        'employee__first_name', 'employee__last_name', 
        'employee__employee_id', 'notes'
    ]
    
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('employee', 'date', 'status')
        }),
        ('Время работы', {
            'fields': ('entry_time', 'exit_time', 'hours_worked')
        }),
        ('Устройства', {
            'fields': ('entry_device', 'exit_device'),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('is_manual_entry', 'is_corrected', 'notes', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['hours_worked', 'created_at', 'updated_at']
    
    list_per_page = 50
    ordering = ['-date', 'employee__last_name']
    
    def get_employee_name(self, obj):
        """Имя сотрудника с отделом"""
        return format_html(
            '<div><strong>{}</strong><br><small style="color: #666;">{}</small></div>',
            obj.employee.get_full_name(),
            obj.employee.department
        )
    get_employee_name.short_description = 'Сотрудник'
    get_employee_name.admin_order_field = 'employee__last_name'
    
    def get_hours_display(self, obj):
        """Отображение отработанных часов"""
        if obj.hours_worked:
            hours = int(obj.hours_worked)
            minutes = int((obj.hours_worked - hours) * 60)
            color = '#4caf50' if obj.is_full_day() else '#ff9800'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}ч {}м</span>',
                color, hours, minutes
            )
        return format_html('<span style="color: #999;">—</span>')
    get_hours_display.short_description = 'Часы'
    get_hours_display.admin_order_field = 'hours_worked'
    
    def get_status_display(self, obj):
        """Цветное отображение статуса"""
        color = obj.get_status_display_color()
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_status_display()
        )
    get_status_display.short_description = 'Статус'
    get_status_display.admin_order_field = 'status'
    
    def get_overtime_display(self, obj):
        """Отображение сверхурочных"""
        if obj.is_overtime():
            overtime = obj.get_overtime_hours()
            return format_html(
                '<span style="color: #2196f3; font-weight: bold;">+{:.1f}ч</span>',
                overtime
            )
        return ''
    get_overtime_display.short_description = 'Сверхурочные'
    
    # Действия
    actions = ['mark_as_corrected', 'export_worktime_report']
    
    def mark_as_corrected(self, request, queryset):
        """Отметить как скорректированные"""
        updated = queryset.update(is_corrected=True, created_by=request.user)
        self.message_user(
            request,
            f'Отмечено как скорректированные: {updated} записей.'
        )
    mark_as_corrected.short_description = "Отметить как скорректированные"
    
    def export_worktime_report(self, request, queryset):
        """Экспорт отчета по рабочему времени"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="worktime_report_{datetime.now().strftime("%Y%m%d")}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'Дата', 'ФИО', 'Табельный номер', 'Отдел', 
            'Приход', 'Уход', 'Часы', 'Статус', 'Примечания'
        ])
        
        for entry in queryset.order_by('date', 'employee__last_name'):
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
        
        self.message_user(
            request,
            f'Экспортировано {queryset.count()} записей рабочего времени.'
        )
        return response
    export_worktime_report.short_description = "Экспорт отчета по времени"


# Настройки админки
admin.site.site_header = "ERP Система - Управление сотрудниками"
admin.site.site_title = "ERP Admin"
admin.site.index_title = "Добро пожаловать в панель управления"