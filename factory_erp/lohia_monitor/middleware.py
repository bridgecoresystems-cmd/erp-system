# lohia_monitor/middleware.py
from django.shortcuts import redirect
from django.urls import reverse


class MasterRedirectMiddleware:
    """
    Middleware для автоматической переадресации мастеров на их страницу.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:
            # Проверяем, является ли пользователь мастером
            if request.user.groups.filter(name__iexact='Мастера').exists():
                # Если мастер заходит на главную страницу или dashboard
                if request.path == '/' or request.path == '/lohia/dashboard/':
                    # Перенаправляем на страницу мастера
                    return redirect('lohia_monitor:master_page')
        
        response = self.get_response(request)
        return response

