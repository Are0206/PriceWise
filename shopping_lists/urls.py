from django.urls import path
from . import views

app_name = 'shopping_lists'

urlpatterns = [
    path('', views.index, name='index'), # Simplificado a 'index'
    path('create/', views.create_shopping_lists, name='create'),
    path('<uuid:pk>/', views.shopping_list_details, name='detail'),
    path('<uuid:pk>/edit/', views.edit_shopping_lists, name='edit'),
    path('<uuid:pk>/delete/', views.delete_shopping_lists, name='delete'),
    path('<uuid:pk>/share/', views.share_shopping_lists, name='share'),
]
