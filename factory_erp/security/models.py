from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from employees.models import Employee

class SecurityLog(models.Model):
    """Лог входов/выходов сотрудников"""
    ACTION_CHOICES = [
        ('in', 'Вход'),
        ('out', 'Выход'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник")
    action = models.CharField(max_length=3, choices=ACTION_CHOICES, verbose_name="Действие")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Время")
    security_guard = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Охранник"
    )
    notes = models.TextField(blank=True, verbose_name="Примечания")
    
    class Meta:
        verbose_name = "Запись охраны"
        verbose_name_plural = "Записи охраны"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_action_display()} - {self.timestamp.strftime('%d.%m.%Y %H:%M')}"

class Shift(models.Model):
    """Смены охраны"""
    guard = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Охранник")
    start_time = models.DateTimeField(verbose_name="Начало смены")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Конец смены")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    
    class Meta:
        verbose_name = "Смена"
        verbose_name_plural = "Смены"
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.guard.username} - {self.start_time.strftime('%d.%m.%Y %H:%M')}"