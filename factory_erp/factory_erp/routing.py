"""
WebSocket URL routing for factory_erp project.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # WebSocket для мониторинга станка Lohia
    re_path(r'ws/lohia/(?P<room_name>\w+)/$', consumers.LohiaConsumer.as_asgi()),
    
    # WebSocket для общих уведомлений
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    
    # WebSocket для мониторинга сотрудников
    re_path(r'ws/employees/$', consumers.EmployeeConsumer.as_asgi()),
    
    # WebSocket для безопасности
    re_path(r'ws/security/$', consumers.SecurityConsumer.as_asgi()),
]
