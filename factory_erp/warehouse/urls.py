from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    path('', views.index, name='index'),
    path('add-tile-type/', views.add_tile_type, name='add_tile_type'),
    path('transaction/', views.add_transaction, name='add_transaction'),
    path('history/', views.transaction_history, name='history'),
]