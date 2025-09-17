from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from .models import TileProduction

logger = logging.getLogger(__name__)

def dashboard(request):
    """Главная страница с счетчиком кафеля"""
    latest_tile = TileProduction.objects.first()
    
    context = {
        'current_count': latest_tile.count if latest_tile else 0,
        'square_meters': latest_tile.square_meters if latest_tile else 0,
        'weight_tons': latest_tile.weight_tons if latest_tile else 0,
        'press_name': 'PH6500',
        'tile_size': '40x80 см',
        'tile_weight': '8.6 кг',
    }
    
    return render(request, 'tile_counter/dashboard.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def esp32_sensor_data(request):
    """API endpoint для ESP32 - увеличение счетчика"""
    try:
        # Увеличиваем счетчик
        tile = TileProduction.increment_count()
        
        logger.info(f"Новый кафель зафиксирован! Общее количество: {tile.count}")
        
        return JsonResponse({
            'success': True,
            'count': tile.count,
            'square_meters': tile.square_meters,
            'weight_tons': tile.weight_tons,
            'message': f'Кафель #{tile.count} зафиксирован'
        })
        
    except Exception as e:
        logger.error(f"Ошибка при обработке данных ESP32: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_current_stats(request):
    """AJAX endpoint для получения текущих данных"""
    latest_tile = TileProduction.objects.first()
    
    if latest_tile:
        data = {
            'success': True,
            'count': latest_tile.count,
            'square_meters': latest_tile.square_meters,
            'weight_tons': latest_tile.weight_tons,
            'timestamp': latest_tile.timestamp.strftime('%H:%M:%S'),
            'date': latest_tile.timestamp.strftime('%d.%m.%Y')
        }
    else:
        data = {
            'success': True,
            'count': 0,
            'square_meters': 0,
            'weight_tons': 0,
            'timestamp': '',
            'date': ''
        }
    
    return JsonResponse(data)

@csrf_exempt  
@require_http_methods(["POST"])
def reset_counter(request):
    """Сброс счетчика (для новой смены)"""
    try:
        TileProduction.reset_count()
        logger.info("Счетчик кафеля сброшен")
        
        return JsonResponse({
            'success': True,
            'message': 'Счетчик сброшен',
            'count': 0
        })
        
    except Exception as e:
        logger.error(f"Ошибка при сбросе счетчика: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)