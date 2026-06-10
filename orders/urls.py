from django.urls import path
from . import views
from .views import (
    CreateCheckoutSessionAPIView,
    OrderListAPIView,
    OrderDetailAPIView,
    CancelOrderAPIView
)

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_page, name='checkout'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),

    path('my-orders/', views.my_orders_page, name='my_orders'),
    path('my-orders/<int:order_id>/', views.order_detail_page, name='order_detail'),

    path('api/create-checkout-session/', CreateCheckoutSessionAPIView.as_view(), name='create-checkout-session'),
    path('api/orders/', OrderListAPIView.as_view(), name='orders-api-list'),
    path('api/orders/<int:order_id>/', OrderDetailAPIView.as_view(), name='orders-api-detail'),
    path('api/cancel/<int:order_id>/', CancelOrderAPIView.as_view(), name='cancel-order'),
]