from django.db import models
from django.utils import timezone

class TileProduction(models.Model):
    # Основные данные
    timestamp = models.DateTimeField(default=timezone.now)
    count = models.IntegerField(default=0)
    
    # Константы для кафеля 40x80 см, 8.6 кг
    TILE_AREA = 0.32      # м² (40см * 80см = 0.32 м²)
    TILE_WEIGHT = 8.6     # кг
    
    # Дополнительная информация
    press_name = models.CharField(max_length=50, default="PH6500")
    tile_size = models.CharField(max_length=20, default="40x80 см")
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"Кафель #{self.count} - {self.timestamp.strftime('%H:%M:%S')}"
    
    @property
    def square_meters(self):
        """Расчет квадратных метров"""
        return round(self.count * self.TILE_AREA, 2)
    
    @property
    def weight_tons(self):
        """Расчет веса в тоннах"""
        total_weight_kg = self.count * self.TILE_WEIGHT
        return round(total_weight_kg / 1000, 3)
    
    @classmethod
    def get_current_count(cls):
        """Получить текущий счетчик"""
        latest = cls.objects.first()
        return latest.count if latest else 0
    
    @classmethod
    def increment_count(cls):
        """Увеличить счетчик на 1"""
        current_count = cls.get_current_count()
        new_count = current_count + 1
        
        # Создаем новую запись
        tile = cls.objects.create(count=new_count)
        return tile
    
    @classmethod
    def reset_count(cls):
        """Сброс счетчика (для новой смены)"""
        cls.objects.create(count=0)
        return cls.objects.first()