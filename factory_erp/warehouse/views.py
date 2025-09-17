from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from .models import TileType, Stock, Transaction

def index(request):
    """Главная страница склада с остатками"""
    search = request.GET.get('search', '')
    
    # Получаем все типы кафеля с остатками
    tile_types = TileType.objects.all()
    
    if search:
        tile_types = tile_types.filter(
            Q(name__icontains=search) |
            Q(article__icontains=search) |
            Q(size__icontains=search)
        )
    
    # Подготавливаем данные для таблицы
    stock_data = []
    total_value = 0
    total_weight = 0
    
    for tile_type in tile_types:
        stock_quantity = tile_type.get_current_stock()
        if stock_quantity > 0 or not search:  # Показываем пустые остатки только без поиска
            item_weight = stock_quantity * tile_type.weight_per_piece
            item_value = stock_quantity * tile_type.price_per_piece
            
            stock_data.append({
                'tile_type': tile_type,
                'quantity': stock_quantity,
                'weight': item_weight,
                'value': item_value
            })
            
            total_weight += item_weight
            total_value += item_value
    
    context = {
        'stock_data': stock_data,
        'total_weight': total_weight,
        'total_value': total_value,
        'search': search,
        'tile_types_for_select': TileType.objects.all()  # Для селекта в модальных окнах
    }
    
    return render(request, 'warehouse/index.html', context)


def add_tile_type(request):
    """Добавление нового типа кафеля"""
    if request.method == 'POST':
        try:
            name = request.POST['name'].strip()
            size = request.POST['size'].strip()
            weight = float(request.POST['weight'])
            price = float(request.POST['price'])
            article = request.POST['article'].strip()
            
            if not all([name, size, article]):
                messages.error(request, 'Все поля обязательны для заполнения!')
                return redirect('warehouse:index')
            
            # Проверяем уникальность артикула
            if TileType.objects.filter(article=article).exists():
                messages.error(request, f'Артикул {article} уже существует!')
                return redirect('warehouse:index')
            
            tile_type = TileType.objects.create(
                name=name,
                size=size,
                weight_per_piece=weight,
                price_per_piece=price,
                article=article
            )
            
            messages.success(request, f'Добавлен новый тип кафеля: {tile_type}')
            
        except ValueError:
            messages.error(request, 'Неверный формат числовых данных!')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    return redirect('warehouse:index')


@login_required
def add_transaction(request):
    """Добавление прихода/расхода"""
    if request.method == 'POST':
        try:
            tile_type_id = request.POST['tile_type']
            operation = request.POST['operation']  # 'IN' or 'OUT'
            quantity = int(request.POST['quantity'])
            comment = request.POST.get('comment', '').strip()
            
            if quantity <= 0:
                messages.error(request, 'Количество должно быть больше 0!')
                return redirect('warehouse:index')
            
            tile_type = get_object_or_404(TileType, id=tile_type_id)
            
            # Проверяем остатки при расходе
            if operation == 'OUT':
                current_stock = tile_type.get_current_stock()
                if quantity > current_stock:
                    messages.error(request, f'Недостаточно остатков! Доступно: {current_stock} шт.')
                    return redirect('warehouse:index')
            
            # Создаем транзакцию
            transaction = Transaction.objects.create(
                tile_type=tile_type,
                operation=operation,
                quantity=quantity,
                comment=comment,
                user=request.user
            )
            
            operation_name = 'Приход' if operation == 'IN' else 'Расход'
            sign = '+' if operation == 'IN' else '-'
            messages.success(request, f'{operation_name}: {tile_type} {sign}{quantity} шт.')
            
        except ValueError:
            messages.error(request, 'Неверный формат количества!')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    return redirect('warehouse:index')


def transaction_history(request):
    """История операций"""
    tile_type_filter = request.GET.get('tile_type')
    operation_filter = request.GET.get('operation')
    
    transactions = Transaction.objects.all()
    
    if tile_type_filter:
        transactions = transactions.filter(tile_type_id=tile_type_filter)
    
    if operation_filter:
        transactions = transactions.filter(operation=operation_filter)
    
    # Пагинация (последние 100 записей)
    transactions = transactions[:100]
    
    context = {
        'transactions': transactions,
        'tile_types': TileType.objects.all(),
        'selected_tile_type': tile_type_filter,
        'selected_operation': operation_filter
    }
    
    return render(request, 'warehouse/history.html', context)