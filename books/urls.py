from django.urls import path
from . import views
from .views import (
    BookListCreateAPIView,
    BookRetrieveUpdateDestroyAPIView,
    CategoryListAPIView,
    FavoriteListAPIView,
    ToggleFavoriteAPIView
)
app_name = 'books'

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('carte/<slug:slug>/', views.book_detail, name='book_detail'),

    path('api/books/', BookListCreateAPIView.as_view(), name='book-api-list'),
    path('api/books/<slug:slug>/', BookRetrieveUpdateDestroyAPIView.as_view(), name='book-api-detail'),

    path('api/favorites/', FavoriteListAPIView.as_view(), name='favorite-api-list'),
    path('api/favorites/toggle/<slug:slug>/', ToggleFavoriteAPIView.as_view(), name='favorite-api-toggle'),

    path('carte/<slug:slug>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    path('api/categories/', CategoryListAPIView.as_view(), name='category-api-list'),
]