# employees/urls.py
from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    # Главная страница с перенаправлением по ролям
    path('', views.HomeView.as_view(), name='index'),
    path('security-display/', views.SecurityDisplayView.as_view(), name='security_display'),
    
    # Управление сотрудниками
    path('list/', views.EmployeeListView.as_view(), name='employee_list'),
    path('add/', views.EmployeeCreateView.as_view(), name='employee_add'),
    path('edit/<int:pk>/', views.EmployeeUpdateView.as_view(), name='employee_edit'),
    path('delete/<int:pk>/', views.employee_delete_ajax, name='employee_delete'),
    path('employee/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    
    # Рабочее время
    path('worktime/', views.WorkTimeListView.as_view(), name='worktime_list'),
    path('worktime/delete/<int:entry_id>/', views.worktime_entry_delete, name='worktime_delete'),
    path('worktime/detail/<int:entry_id>/', views.worktime_entry_detail, name='worktime_detail'),
    path('worktime/update/<int:entry_id>/', views.worktime_entry_update, name='worktime_update'),
    path('worktime/create/', views.worktime_entry_create, name='worktime_create'),
    path('worktime/stats/', views.worktime_stats_api, name='worktime_stats'),
    
    # API endpoints для ESP32
    # Добавь эту строку в urlpatterns
    path('api/employee-search/', views.employee_search_api, name='employee_search'),
    path('api/rfid-scan/', views.rfid_scan, name='rfid_scan'),
    path('api/employee/<int:employee_id>/', views.employee_detail_api, name='employee_detail_api'),
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    path('api/latest-access/', views.latest_access_api, name='latest_access_api'),
    path('api/worktime-latest/', views.worktime_latest_api, name='worktime_latest_api'),
    
    # AJAX Polling API
    path('api/worktime-polling/', views.worktime_polling_api, name='worktime_polling'),
]