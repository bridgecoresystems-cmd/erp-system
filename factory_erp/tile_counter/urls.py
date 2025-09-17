from django.urls import path
from . import views

app_name = 'tile_counter'

urlpatterns = [
    # Главная страница счетчика
    path('', views.dashboard, name='dashboard'),
    
    # API для ESP32
    path('api/sensor/', views.esp32_sensor_data, name='esp32_sensor'),
    
    # AJAX endpoint для frontend
    path('api/stats/', views.get_current_stats, name='current_stats'),
    
    # Сброс счетчика
    path('api/reset/', views.reset_counter, name='reset_counter'),
]