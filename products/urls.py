from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:pk>/', views.view_product_details, name='detail'),
    path('<int:pk>/compare/', views.compare_product_prices, name='compare'),
    path('favorite/toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('<int:pk>/review/', views.submit_review, name='submit_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    
    path('supermarkets/', views.supermarkets_index, name='supermarkets_index'),
    path('supermarkets/<int:pk>', views.supermarkets_details, name='supermarkets_details'),
    path('supermarkets/<int:pk>/review/', views.submit_supermarket_review, name='submit_supermarket_review'),
    path('supermarkets/review/<int:review_id>/delete/', views.delete_supermarket_review, name='delete_supermarket_review'),
]