from django.urls import path
from . import views
from .views import (
    CartItemListAPIView,
    AddToCartAPIView,
    UpdateCartItemAPIView,
    RemoveCartItemAPIView
)

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),

    path('api/items/', CartItemListAPIView.as_view(), name='cart-api-items'),
    path('api/add/', AddToCartAPIView.as_view(), name='cart-api-add'),
    path('api/update/<int:item_id>/', UpdateCartItemAPIView.as_view(), name='cart-api-update'),
    path('api/remove/<int:item_id>/', RemoveCartItemAPIView.as_view(), name='cart-api-remove'),
]