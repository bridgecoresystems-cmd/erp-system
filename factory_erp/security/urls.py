
from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    path('', views.security_dashboard, name='dashboard'),
    path('log/<int:employee_id>/<str:action>/', views.log_action, name='log_action'),
    path('shift/start/', views.start_shift, name='start_shift'),
    path('shift/end/', views.end_shift, name='end_shift'),
    path('export/excel/', views.export_logs_excel, name='export_excel'),
    path('reports/logs/', views.logs_report, name='logs_report'),
    
    # API endpoints
    path('api/latest-access/', views.latest_access_api, name='latest_access_api'),
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/scan/', views.rfid_scan_api, name='rfid_scan_api'),
]