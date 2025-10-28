# lohia_monitor/urls.py
from django.urls import path
from . import views

app_name = 'lohia_monitor'

urlpatterns = [
    # API для ESP32
    path('api/shift/start/', views.shift_start_api, name='shift_start_api'),
    path('api/shift/end/', views.shift_end_api, name='shift_end_api'),
    path('api/pulse/update/', views.pulse_update_api, name='pulse_update_api'),
    path('api/maintenance/call/', views.maintenance_call_api, name='maintenance_call_api'),
    path('api/maintenance/start/', views.maintenance_start_api, name='maintenance_start_api'),
    path('api/maintenance/end/', views.maintenance_end_api, name='maintenance_end_api'),
    
    # Веб-интерфейс для начальника цеха
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('machine/<int:machine_id>/', views.MachineDetailView.as_view(), name='machine_detail'),
    path('shifts/', views.ShiftsHistoryView.as_view(), name='shifts_history'),
    path('maintenance/', views.MaintenanceHistoryView.as_view(), name='maintenance_history'),
    path('stats/', views.MachineStatsView.as_view(), name='machine_stats'),
    path('master/', views.master_page, name='master_page'),
    
    # API для AJAX обновления
    path('api/dashboard-status/', views.dashboard_status_api, name='dashboard_status_api'),
    path('api/dashboard-status-all/', views.dashboard_status_all_api, name='dashboard_status_all_api'),
    path('api/maintenance-history/', views.maintenance_history_api, name='maintenance_history_api'),
    path('api/shifts-history/', views.shifts_history_api, name='shifts_history_api'),
    path('api/machine/<int:machine_id>/detail/', views.machine_detail_api, name='machine_detail_api'),
    path('api/machine-stats/', views.machine_stats_api, name='machine_stats_api'),
]
