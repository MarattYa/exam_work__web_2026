from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_collections, name='my_collections'),
    path('add/', views.collection_create, name='collection_create'),
    path('<int:pk>/', views.collection_detail, name='collection_detail'),
]