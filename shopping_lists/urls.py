from django.urls import path
from . import views

app_name = 'shopping_lists'

urlpatterns = [
    path('', views.index, name='index'), # Simplificado a 'index'
    path('create/', views.create_shopping_lists, name='create'),
    path('<int:pk>/', views.shopping_list_details, name='detail'),
    path('<int:pk>/edit/', views.shopping_list_edit, name='edit'),
    path('<int:pk>/delete/', views.delete_shopping_lists, name='delete'),
]
