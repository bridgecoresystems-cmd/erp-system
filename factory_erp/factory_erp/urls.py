# factory_erp/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

def redirect_to_employees(request):
    """Редирект с главной страницы на employees с проверкой групп"""
    if request.user.is_authenticated:
        # Проверяем группы пользователя и перенаправляем соответственно
        if request.user.groups.filter(name='HR_Admins').exists():
            return redirect('employees:employee_list')
        elif request.user.groups.filter(name='HR_Users').exists():
            return redirect('employees:worktime_list')
        elif request.user.groups.filter(name='Security_Users').exists():
            return redirect('employees:security_display')
        else:
            # Пользователь без группы - на общую страницу
            return redirect('employees:employee_list')
    else:
        # Неавторизованный пользователь - на логин
        return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_employees, name='home'),
    path('employees/', include('employees.urls')),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),      
    path('tile_counter/', include('tile_counter.urls')),
    path('warehouse/', include('warehouse.urls')),
]

# Медиа файлы для разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)