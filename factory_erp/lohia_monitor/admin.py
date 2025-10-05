# lohia_monitor/admin.py
from django.contrib import admin
from .models import Machine, Shift, MaintenanceCall, PulseLog

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['name', 'esp32_id', 'status', 'current_operator', 'current_pulse_count', 'current_meters', 'is_active']
    list_filter = ['status', 'is_active']
    search_fields = ['name', 'esp32_id']
    readonly_fields = ['current_pulse_count', 'current_meters', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'esp32_id', 'meters_per_pulse', 'is_active')
        }),
        ('Текущее состояние', {
            'fields': ('status', 'current_operator', 'current_pulse_count', 'current_meters')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['operator', 'machine', 'start_time', 'end_time', 'total_pulses', 'total_meters', 'status', 'duration_hours']
    list_filter = ['status', 'machine', 'start_time']
    search_fields = ['operator__first_name', 'operator__last_name', 'machine__name']
    readonly_fields = ['total_meters', 'duration', 'duration_hours', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('operator', 'machine', 'start_time', 'end_time', 'status')
        }),
        ('Производство', {
            'fields': ('total_pulses', 'total_meters')
        }),
        ('Системная информация', {
            'fields': ('duration', 'duration_hours', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MaintenanceCall)
class MaintenanceCallAdmin(admin.ModelAdmin):
    list_display = ['machine', 'operator', 'call_time', 'master', 'status', 'response_time', 'repair_time']
    list_filter = ['status', 'machine', 'call_time']
    search_fields = ['operator__first_name', 'operator__last_name', 'master__first_name', 'master__last_name', 'machine__name']
    readonly_fields = ['response_time', 'repair_time', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('machine', 'operator', 'call_time', 'status')
        }),
        ('Ремонт', {
            'fields': ('master', 'start_time', 'end_time', 'description')
        }),
        ('Временные показатели', {
            'fields': ('response_time', 'repair_time'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PulseLog)
class PulseLogAdmin(admin.ModelAdmin):
    list_display = ['machine', 'shift', 'timestamp', 'pulse_count', 'total_pulses', 'meters_produced']
    list_filter = ['machine', 'timestamp']
    search_fields = ['machine__name']
    readonly_fields = ['meters_produced']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('machine', 'shift', 'timestamp')
        }),
        ('Производство', {
            'fields': ('pulse_count', 'total_pulses', 'meters_produced')
        }),
    )