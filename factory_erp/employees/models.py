# employees/models.py
from django.db import models
from django.contrib.auth.models import User
from datetime import date, datetime, timedelta
from django.core.validators import RegexValidator


class Employee(models.Model):
    # Основные данные сотрудника
    rfid_uid = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="RFID UID")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=50, blank=True, verbose_name="Отчество")

    # Персональные данные
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")

    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name="Пол")

    MARITAL_STATUS_CHOICES = [
        ('single', 'Холост/Не замужем'),
        ('married', 'Женат/Замужем'),
        ('divorced', 'Разведен(а)'),
        ('widowed', 'Вдовец/Вдова'),
    ]
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        blank=True,
        verbose_name="Семейное положение"
    )

    # Контактные данные
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Адрес проживания")

    # Паспортные данные
    passport_series_regex = RegexValidator(
        regex=r'^[IVXLC]-[A-Z]{2}$',
        message="Серия паспорта должна быть в формате: I-AH, II-MR и т.д."
    )
    passport_series = models.CharField(validators=[passport_series_regex], max_length=4, blank=True, verbose_name="Серия паспорта")

    passport_number_regex = RegexValidator(
        regex=r'^\d{6}$',
        message="Номер паспорта должен содержать 6 цифр"
    )
    passport_number = models.CharField(validators=[passport_number_regex], max_length=6, blank=True, verbose_name="Номер паспорта")

    passport_issued_date = models.DateField(null=True, blank=True, verbose_name="Дата выдачи паспорта")
    passport_issued_by = models.TextField(blank=True, verbose_name="Кем выдан паспорт")

    # Налоговые и страховые данные
    inn_regex = RegexValidator(
        regex=r'^\d{10}$|^\d{12}$',
        message="ИНН должен содержать 10 или 12 цифр."
    )
    inn = models.CharField(validators=[inn_regex], max_length=12, blank=True, verbose_name="ИНН")

    snils_regex = RegexValidator(
        regex=r'^\d{11}$',
        message="СНИЛС должен содержать 11 цифр"
    )
    snils = models.CharField(validators=[snils_regex], max_length=11, blank=True, verbose_name="СНИЛС")

    # Рабочие данные
    department = models.CharField(max_length=100, verbose_name="Цех")
    position = models.CharField(max_length=100, verbose_name="Должность")
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="Табельный номер")

    # Фото сотрудника
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True, verbose_name="Фото")

    # Статус
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    # Даты
    hire_date = models.DateField(verbose_name="Дата приема")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.department})"

    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    def get_photo_url(self):
        return self.photo.url if self.photo else '/static/images/no-photo.png'

    def get_age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None

    def get_passport_full(self):
        if self.passport_series and self.passport_number:
            return f"{self.passport_series} {self.passport_number}"
        return "Не указан"

    def get_contact_info(self):
        contacts = []
        if self.phone:
            contacts.append(f"Тел: {self.phone}")
        if self.email:
            contacts.append(f"Email: {self.email}")
        return ", ".join(contacts) if contacts else "Контакты не указаны"


class CardAccess(models.Model):
    """Модель для логирования касаний карт"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Сотрудник")
    rfid_uid = models.CharField(max_length=20, verbose_name="RFID UID")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время касания")

    # Дополнительная информация
    device_id = models.CharField(max_length=50, default="ESP32-001", verbose_name="Устройство")
    success = models.BooleanField(default=True, verbose_name="Успешно")

    class Meta:
        verbose_name = "Касание карты"
        verbose_name_plural = "Касания карт"
        ordering = ['-timestamp']

    def __str__(self):
        if self.employee:
            return f"{self.employee.get_full_name()} - {self.timestamp.strftime('%d.%m.%Y %H:%M:%S')}"
        return f"Неизвестная карта {self.rfid_uid} - {self.timestamp.strftime('%d.%m.%Y %H:%M:%S')}"
    
class WorkTimeEntry(models.Model):
    """Модель для учета рабочего времени сотрудников"""
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник")
    date = models.DateField(verbose_name="Дата")
    
    # Время входа и выхода
    entry_time = models.TimeField(null=True, blank=True, verbose_name="Время прихода")
    exit_time = models.TimeField(null=True, blank=True, verbose_name="Время ухода")
    
    # Рассчитанные поля
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Отработано часов")
    
    # Статус рабочего дня
    STATUS_CHOICES = [
        ('present', 'Присутствует'),
        ('absent', 'Отсутствует'),
        ('sick', 'Больничный'),
        ('vacation', 'Отпуск'),
        ('partial', 'Частичный день'),
        ('late', 'Опоздание'),
        ('early_leave', 'Ранний уход'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present', verbose_name="Статус")
    
    # Устройства входа/выхода
    entry_device = models.CharField(max_length=50, blank=True, verbose_name="Устройство входа")
    exit_device = models.CharField(max_length=50, blank=True, verbose_name="Устройство выхода")
    
    # Флаги для контроля
    is_manual_entry = models.BooleanField(default=False, verbose_name="Ручной ввод")
    is_corrected = models.BooleanField(default=False, verbose_name="Скорректировано HR")
    
    # Комментарии
    notes = models.TextField(blank=True, verbose_name="Примечания")
    
    # Служебные поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Создано пользователем")
    
    class Meta:
        verbose_name = "Рабочее время"
        verbose_name_plural = "Рабочее время"
        ordering = ['-date', 'employee__last_name']
        unique_together = ['employee', 'date']  # Одна запись на сотрудника в день
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date.strftime('%d.%m.%Y')}"
    
    def save(self, *args, **kwargs):
        """Автоматический расчет часов при сохранении"""
        if self.entry_time and self.exit_time:
            # Создаем datetime объекты для расчета
            entry_datetime = datetime.combine(self.date, self.entry_time)
            exit_datetime = datetime.combine(self.date, self.exit_time)
            
            # Если выход на следующий день (ночная смена)
            if self.exit_time < self.entry_time:
                exit_datetime += timedelta(days=1)
            
            # Рассчитываем часы
            time_diff = exit_datetime - entry_datetime
            self.hours_worked = round(time_diff.total_seconds() / 3600, 2)
            
            # Определяем статус
            if self.hours_worked < 4:
                self.status = 'partial'
            elif self.entry_time > datetime.strptime('09:30', '%H:%M').time():
                self.status = 'late'
            elif self.hours_worked < 7:
                self.status = 'early_leave'
            else:
                self.status = 'present'
        
        super().save(*args, **kwargs)
    
    def get_hours_display(self):
        """Красивое отображение часов"""
        if self.hours_worked:
            hours = int(self.hours_worked)
            minutes = int((self.hours_worked - hours) * 60)
            if minutes > 0:
                return f"{hours}ч {minutes}мин"
            return f"{hours}ч"
        return "0ч"

    def get_status_display_color(self):
        """Цвет для отображения статуса"""
        status_colors = {
            'present': '#4caf50',      # зеленый
            'absent': '#f44336',       # красный
            'sick': '#ff9800',         # оранжевый
            'vacation': '#2196f3',     # синий
            'partial': '#ff5722',      # красно-оранжевый
            'late': '#ff9800',         # оранжевый
            'early_leave': '#ff5722',  # красно-оранжевый
        }
        return status_colors.get(self.status, '#666')
    
    def is_full_day(self):
        """Проверка на полный рабочий день (7+ часов)"""
        return self.hours_worked and self.hours_worked >= 7
    
    def is_overtime(self):
        """Проверка на сверхурочные (более 8 часов)"""
        return self.hours_worked and self.hours_worked > 8
    
    def get_overtime_hours(self):
        """Количество сверхурочных часов"""
        if self.is_overtime():
            return self.hours_worked - 8
        return 0
    
    def calculate_hours_worked(self):
        """Расчет отработанных часов с учетом обеда"""
        if self.entry_time and self.exit_time:
            # Создаем datetime объекты для расчета
            today = datetime.now().date()
            entry_datetime = datetime.combine(today, self.entry_time)
            exit_datetime = datetime.combine(today, self.exit_time)
            
            # Если ушел на следующий день (ночная смена)
            if self.exit_time < self.entry_time:
                exit_datetime += timedelta(days=1)
            
            # Вычисляем общее время
            total_time = exit_datetime - entry_datetime
            
            # Автоматически вычитаем обед если работал больше 6 часов
            if total_time > timedelta(hours=6):
                total_time -= timedelta(hours=2)  # обед 2 часа
            
            return max(0, total_time.total_seconds() / 3600)  # не меньше 0
        return 0
    
    def save(self, *args, **kwargs):
        """Автоматически пересчитываем часы при сохранении"""
        if self.entry_time and self.exit_time:
            self.hours_worked = self.calculate_hours_worked()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_monthly_stats(cls, employee, year, month):
        """Статистика по месяцу для сотрудника"""
        entries = cls.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month
        )
        
        total_hours = sum(entry.hours_worked or 0 for entry in entries)
        working_days = entries.filter(status='present').count()
        late_days = entries.filter(status='late').count()
        overtime_hours = sum(entry.get_overtime_hours() for entry in entries)
        
        return {
            'total_hours': total_hours,
            'working_days': working_days,
            'late_days': late_days,
            'overtime_hours': overtime_hours,
            'entries': entries
        }
