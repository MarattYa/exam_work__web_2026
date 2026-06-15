from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='home'),
    path('books/add/', views.book_create, name='book_create'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_update, name='book_update'),
    path('books/<int:pk>/delete/', views.book_delete, name='book_delete'),
    path('books/<int:pk>/review/', views.review_create, name='review_create'),
    path('books/<int:pk>/review/edit/', views.review_update, name='review_update'),
    path('books/<int:pk>/add-to-collection/', views.add_to_collection, name='add_to_collection'),
]