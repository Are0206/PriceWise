from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:pk>/', views.view_product_details, name='detail'),
    path('<int:pk>/compare/', views.compare_product_prices, name='compare'),
    path('favorite/toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
]