"""
WebSocket URL routing for factory_erp project.
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # WebSocket для мониторинга станка Lohia
    path('ws/lohia/<str:room_name>/', consumers.LohiaConsumer.as_asgi()),
    
    # WebSocket для общих уведомлений
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
    
    # WebSocket для мониторинга сотрудников
    path('ws/employees/', consumers.EmployeeConsumer.as_asgi()),
    
    # WebSocket для безопасности
    path('ws/security/', consumers.SecurityConsumer.as_asgi()),
]
