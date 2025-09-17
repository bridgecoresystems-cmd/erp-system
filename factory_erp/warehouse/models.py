from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TileType(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    size = models.CharField(max_length=50, verbose_name="Размер")  # 40x80, 30x60
    weight_per_piece = models.DecimalField(max_digits=8, decimal_places=3, verbose_name="Вес штуки (кг)")
    price_per_piece = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за штуку")
    article = models.CharField(max_length=100, unique=True, verbose_name="Артикул")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Тип кафеля"
        verbose_name_plural = "Типы кафеля"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} {self.size}"

    def get_current_stock(self):
        """Получить текущий остаток"""
        stock, created = Stock.objects.get_or_create(tile_type=self)
        return stock.quantity

    def get_total_value(self):
        """Общая стоимость остатков"""
        return self.get_current_stock() * self.price_per_piece


class Stock(models.Model):
    tile_type = models.OneToOneField(TileType, on_delete=models.CASCADE, verbose_name="Тип кафеля")
    quantity = models.IntegerField(default=0, verbose_name="Количество штук")
    
    class Meta:
        verbose_name = "Остаток"
        verbose_name_plural = "Остатки"

    def __str__(self):
        return f"{self.tile_type} - {self.quantity} шт"

    def get_total_weight(self):
        """Общий вес остатка"""
        return self.quantity * self.tile_type.weight_per_piece

    def get_total_value(self):
        """Общая стоимость остатка"""
        return self.quantity * self.tile_type.price_per_piece


class Transaction(models.Model):
    OPERATION_CHOICES = [
        ('IN', 'Приход'),
        ('OUT', 'Расход'),
    ]

    tile_type = models.ForeignKey(TileType, on_delete=models.CASCADE, verbose_name="Тип кафеля")
    operation = models.CharField(max_length=3, choices=OPERATION_CHOICES, verbose_name="Операция")
    quantity = models.IntegerField(verbose_name="Количество")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата/время")

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.operation == 'IN' else '-'
        return f"{self.tile_type} {sign}{self.quantity} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"

    def save(self, *args, **kwargs):
        """При сохранении транзакции обновляем остатки"""
        super().save(*args, **kwargs)
        
        # Получаем или создаем остаток
        stock, created = Stock.objects.get_or_create(tile_type=self.tile_type)
        
        # Обновляем количество
        if self.operation == 'IN':
            stock.quantity += self.quantity
        else:  # OUT
            stock.quantity -= self.quantity
            # Защита от отрицательных остатков
            if stock.quantity < 0:
                stock.quantity = 0
        
        stock.save()