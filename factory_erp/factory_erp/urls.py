from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.views.generic import RedirectView


def redirect_to_employees(request):
    """Редирект с главной страницы на соответствующую панель в зависимости от группы пользователя"""
    if request.user.is_authenticated:
        user = request.user
        
        # Отладочная информация - можно убрать после исправления
        print(f"DEBUG: User {user.username} is authenticated")
        print(f"DEBUG: User groups: {[g.name for g in user.groups.all()]}")
        print(f"DEBUG: Is superuser: {user.is_superuser}")
        
        # Суперпользователь - на админку
        if user.is_superuser:
            print("DEBUG: Redirecting superuser to admin")
            return redirect('admin:index')
        
        # Проверяем группы пользователя и перенаправляем соответственно
        user_groups = [g.name for g in user.groups.all()]
        
        # Приоритет перенаправлений по группам
        if 'HR_Admins' in user_groups:
            print("DEBUG: Redirecting HR_Admins to employees:employee_list")
            return redirect('employees:employee_list')
        elif 'HR_Users' in user_groups:
            print("DEBUG: Redirecting HR_Users to employees:worktime_list")
            return redirect('employees:worktime_list')
        elif 'Security' in user_groups:
            print("DEBUG: Redirecting Security user to security:dashboard")
            return redirect('security:dashboard')
        elif 'Security_Users' in user_groups:
            print("DEBUG: Redirecting Security_Users to employees:security_display")
            return redirect('employees:security_display')
        else:
            print("DEBUG: User has no matching groups, redirecting to employees:home")
            return redirect('employees:home')
    else:
        print("DEBUG: User not authenticated, redirecting to login")
        return redirect('login')


def favicon_view(request):
    """Обработчик для favicon.ico - использует ваш файл"""
    import os
    from django.http import FileResponse
    
    # Ищем favicon в staticfiles
    favicon_path = os.path.join(settings.STATIC_ROOT, 'images', 'favicon.ico')
    
    if os.path.exists(favicon_path):
        return FileResponse(open(favicon_path, 'rb'), content_type='image/x-icon')
    else:
        # Fallback - создаем простой favicon
        from PIL import Image, ImageDraw
        import io
        
        img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([4, 4, 28, 28], fill=(52, 152, 219), outline=(41, 128, 185))
        
        buffer = io.BytesIO()
        img.save(buffer, format='ICO', sizes=[(32, 32)])
        buffer.seek(0)
        
        return HttpResponse(buffer.getvalue(), content_type='image/x-icon')


def websocket_test_view(request):
    """Тестовая страница для WebSocket"""
    return render(request, 'websocket_test.html')


def websocket_simple_test_view(request):
    """Простая тестовая страница для WebSocket"""
    import os
    from django.http import FileResponse
    
    # Читаем HTML файл напрямую
    html_path = os.path.join(settings.BASE_DIR, '..', 'websocket_simple_test.html')
    
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    else:
        return HttpResponse("Файл теста не найден", status=404)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_employees, name='home'),
    
    # Favicon
    path('favicon.ico', favicon_view, name='favicon'),
    
    # Основные приложения
    path('employees/', include('employees.urls')),
    path('security/', include('security.urls')),  # Новое приложение безопасности
    path('lohia/', include('lohia_monitor.urls')),  # Мониторинг станка Lohia
    
    # Аутентификация
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # WebSocket тест
    path('websocket-test/', websocket_test_view, name='websocket_test'),
    path('websocket-simple/', websocket_simple_test_view, name='websocket_simple_test'),
]

# Медиа файлы для разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Добавляем staticfiles для доступа к логотипам
    urlpatterns += static('/staticfiles/', document_root=settings.STATIC_ROOT)