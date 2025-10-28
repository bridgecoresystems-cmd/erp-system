# lohia_monitor/models.py
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from employees.models import Employee
from decimal import Decimal

class Machine(models.Model):
    """Станок Lohia"""
    name = models.CharField(max_length=100, verbose_name="Название станка")
    esp32_id = models.CharField(max_length=50, unique=True, verbose_name="ID ESP32")
    
    # Параметры станка из настроек
    transmit_pulse = models.IntegerField(default=40, verbose_name="Transmit Pulse")
    gear_box_ratio = models.DecimalField(
        max_digits=10, decimal_places=2, 
        default=64.00, 
        verbose_name="Gear box redn ratio"
    )
    sprocket_gear_box = models.IntegerField(default=23, verbose_name="Sprocket gear box")
    sprocket_takeup_roller = models.IntegerField(default=41, verbose_name="Sprocket takeup roller")
    roller_diameter_cm = models.DecimalField(
        max_digits=10, decimal_places=2, 
        default=16.70, 
        verbose_name="Roller Dia. (cm)"
    )
    p_ctrl_ampl = models.IntegerField(default=2, verbose_name="P-Ctrl. Ampl.")
    
    # Вычисляемое значение метров за импульс
    meters_per_pulse = models.DecimalField(
        max_digits=10, decimal_places=6, 
        default=0.0, 
        verbose_name="Метров за импульс (вычисляемое)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    # Текущее состояние
    status = models.CharField(
        max_length=20,
        choices=[
            ('idle', 'Простой'),
            ('working', 'Работает'),
            ('maintenance', 'В ремонте'),
            ('stopped', 'Остановлен'),
        ],
        default='idle',
        verbose_name="Статус"
    )
    current_operator = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Текущий оператор"
    )
    current_pulse_count = models.IntegerField(default=0, verbose_name="Текущий счетчик импульсов")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Станок"
        verbose_name_plural = "Станки"
        indexes = [
            # КРИТИЧНО для высокоскоростных запросов ESP32
            models.Index(fields=['esp32_id', 'is_active'], name='machine_esp32_active'),
            models.Index(fields=['current_operator', 'status'], name='machine_op_status'),
            models.Index(fields=['updated_at'], name='machine_updated'),
        ]
    
    def __str__(self):
        return self.name
    
    def calculate_meters_per_pulse(self):
        """Вычисляет метры за импульс на основе параметров станка"""
        from decimal import Decimal
        
        # Формула: (π * диаметр_ролика_см / 100) / (передаточное_отношение * отношение_зубчатых_колес)
        # π * диаметр_ролика_см / 100 = длина окружности в метрах
        # передаточное_отношение = gear_box_ratio
        # отношение_зубчатых_колес = sprocket_takeup_roller / sprocket_gear_box
        
        pi = Decimal('3.14159265359')
        roller_diameter_m = Decimal(str(self.roller_diameter_cm)) / Decimal('100')  # переводим см в метры
        circumference = pi * roller_diameter_m  # длина окружности ролика
        
        # Общее передаточное отношение
        gear_ratio = Decimal(str(self.gear_box_ratio)) * (Decimal(str(self.sprocket_takeup_roller)) / Decimal(str(self.sprocket_gear_box)))
        
        # Метры за один оборот ролика
        meters_per_revolution = circumference / gear_ratio
        
        # Метры за импульс (если transmit_pulse импульсов = 1 оборот)
        meters_per_pulse = meters_per_revolution / Decimal(str(self.transmit_pulse))
        
        return meters_per_pulse
    
    def save(self, *args, **kwargs):
        """Пересчитывает meters_per_pulse при сохранении (если не задано вручную)"""
        import logging
        logger = logging.getLogger(__name__)
        
        old_value = self.meters_per_pulse
        
        # ТОЛЬКО если meters_per_pulse = 0 (новый станок) - автоматический режим
        if self.meters_per_pulse == Decimal('0'):
            self.meters_per_pulse = self.calculate_meters_per_pulse()
            logger.warning(f"🔄 АВТОПЕРЕСЧЕТ meters_per_pulse: 0 → {self.meters_per_pulse}")
        else:
            logger.info(f"✅ СОХРАНЯЕМ meters_per_pulse: {old_value} (НЕ пересчитываем)")
        
        # Иначе используем заданное вручную значение (НЕ пересчитываем)
        super().save(*args, **kwargs)
        
        # Логируем если значение изменилось
        if old_value != self.meters_per_pulse:
            logger.error(f"❌ ЗНАЧЕНИЕ ИЗМЕНИЛОСЬ! {old_value} → {self.meters_per_pulse}")
            import traceback
            logger.error(f"СТЕК ВЫЗОВОВ:\n{traceback.format_stack()}")
    
    @property
    def current_meters(self):
        """Текущий метраж в метрах"""
        return float(self.current_pulse_count * self.meters_per_pulse)
    
    def start_shift(self, operator):
        """Начать смену"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.warning(f"🚀 START_SHIFT вызван для {self.name}")
        logger.warning(f"   meters_per_pulse ДО: {self.meters_per_pulse}")
        
        self.current_operator = operator
        self.status = 'working'
        self.current_pulse_count = 0
        self.save()
        
        # Перечитываем из БД
        self.refresh_from_db()
        logger.warning(f"   meters_per_pulse ПОСЛЕ: {self.meters_per_pulse}")
        
        # Проверяем что значение больше 0.01 (наш новый датчик)
        if self.meters_per_pulse < Decimal('0.01'):
            logger.error(f"❌ ЗНАЧЕНИЕ СБРОСИЛОСЬ В start_shift()! Стало: {self.meters_per_pulse}")
        else:
            logger.info(f"✅ Значение корректное: {self.meters_per_pulse}")
    
    def end_shift(self):
        """Завершить смену"""
        self.current_operator = None
        self.status = 'idle'
        # НЕ сбрасываем счетчик импульсов - он должен сохраняться
        self.save()
    
    def start_maintenance(self):
        """Начать ремонт"""
        self.status = 'maintenance'
        self.save()
    
    def end_maintenance(self):
        """Завершить ремонт"""
        if self.current_operator:
            self.status = 'working'
        else:
            self.status = 'idle'
        self.save()


class Shift(models.Model):
    """Смена на станке"""
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Оператор")
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, verbose_name="Станок")
    start_time = models.DateTimeField(verbose_name="Начало смены")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Окончание смены")
    total_pulses = models.IntegerField(default=0, verbose_name="Общее количество импульсов")
    total_meters = models.DecimalField(
        max_digits=10, decimal_places=2, 
        default=0, 
        verbose_name="Общий метраж"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Активна'),
            ('completed', 'Завершена'),
        ],
        default='active',
        verbose_name="Статус смены"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Смена"
        verbose_name_plural = "Смены"
        ordering = ['-start_time']
        indexes = [
            # КРИТИЧНО для быстрого поиска активных смен
            models.Index(fields=['machine', 'operator', 'status'], name='shift_mach_op_status'),
            models.Index(fields=['start_time'], name='shift_start_time'),
            models.Index(fields=['status', 'machine'], name='shift_status_mach'),
        ]
    
    def __str__(self):
        return f"{self.operator.get_full_name()} - {self.machine.name} ({self.start_time.strftime('%d.%m.%Y %H:%M')})"
    
    @property
    def duration(self):
        """Длительность смены"""
        if self.end_time:
            return self.end_time - self.start_time
        return timezone.now() - self.start_time
    
    @property
    def duration_hours(self):
        """Длительность смены в часах"""
        duration = self.duration
        return duration.total_seconds() / 3600
    
    def get_duration_display(self):
        """Отображение длительности смены"""
        duration = self.duration
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}:{minutes:02d}"
    
    def complete_shift(self):
        """Завершить смену"""
        self.end_time = timezone.now()
        self.status = 'completed'
        self.save()
    
    def get_current_pulses(self):
        """Получить текущее количество импульсов за смену"""
        return PulseLog.objects.filter(
            machine=self.machine,
            timestamp__gte=self.start_time
        ).aggregate(
            total=Sum('pulse_count')
        )['total'] or 0
    
    def get_efficiency(self):
        """Получить эффективность смены в процентах"""
        current_pulses = self.get_current_pulses()
        target_pulses = 1000  # Можно сделать настраиваемым
        if target_pulses > 0:
            return min(100, (current_pulses / target_pulses) * 100)
        return 0


class MaintenanceCall(models.Model):
    """Вызов мастера"""
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, verbose_name="Станок")
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Оператор")
    call_time = models.DateTimeField(verbose_name="Время вызова")
    master = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='maintenance_calls',
        verbose_name="Мастер"
    )
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="Начало ремонта")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Окончание ремонта")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидает'),
            ('in_progress', 'В работе'),
            ('completed', 'Завершен'),
        ],
        default='pending',
        verbose_name="Статус"
    )
    description = models.TextField(blank=True, verbose_name="Описание проблемы")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Вызов мастера"
        verbose_name_plural = "Вызовы мастера"
        ordering = ['-call_time']
    
    def __str__(self):
        return f"Вызов {self.machine.name} - {self.call_time.strftime('%d.%m.%Y %H:%M')}"
    
    @property
    def response_time(self):
        """Время реакции мастера (от вызова до прибытия)"""
        if self.start_time:
            return self.start_time - self.call_time
        return None
    
    @property
    def repair_time(self):
        """Время ремонта (от прибытия до завершения)"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def get_response_time_display(self):
        """Отображение времени реакции"""
        if self.response_time:
            total_seconds = int(self.response_time.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:02d}"
        return "—"
    
    def get_repair_time_display(self):
        """Отображение времени ремонта"""
        if self.repair_time:
            total_seconds = int(self.repair_time.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:02d}"
        return "—"
    
    def start_maintenance(self, master):
        """Начать ремонт"""
        self.master = master
        self.start_time = timezone.now()
        self.status = 'in_progress'
        self.machine.start_maintenance()
        self.save()
    
    def complete_maintenance(self, description=""):
        """Завершить ремонт"""
        self.end_time = timezone.now()
        self.status = 'completed'
        if description:
            self.description = description
        self.machine.end_maintenance()
        self.save()


class PulseLog(models.Model):
    """Лог импульсов для детальной истории"""
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, verbose_name="Станок")
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, verbose_name="Смена")
    timestamp = models.DateTimeField(verbose_name="Время")
    pulse_count = models.IntegerField(verbose_name="Количество импульсов")
    total_pulses = models.IntegerField(verbose_name="Общее количество импульсов")
    meters_produced = models.DecimalField(
        max_digits=10, decimal_places=2, 
        verbose_name="Произведено метров"
    )
    
    class Meta:
        verbose_name = "Лог импульсов"
        verbose_name_plural = "Логи импульсов"
        ordering = ['-timestamp']
        indexes = [
            # КРИТИЧНО для высокоскоростной записи импульсов
            models.Index(fields=['machine', 'timestamp'], name='pulse_mach_time'),
            models.Index(fields=['shift', 'timestamp'], name='pulse_shift_time'),
            models.Index(fields=['timestamp'], name='pulse_timestamp'),
        ]
    
    def __str__(self):
        return f"{self.machine.name} - {self.timestamp.strftime('%H:%M:%S')} - {self.pulse_count} импульсов"