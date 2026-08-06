from django.urls import path
from . import views

app_name = 'shopping_lists'

urlpatterns = [
    path('', views.shopping_list_index, name='index'),
    path('create/', views.shopping_list_create, name='create'),
    path('<int:pk>/', views.shopping_list_detail, name='detail'),
]