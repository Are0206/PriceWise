from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('<int:pk>/', views.product_detail, name='detail'),
    path('<int:pk>/compare/', views.compare_prices, name='compare'),
]