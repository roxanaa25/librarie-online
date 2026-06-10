from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('book', 'book_title', 'quantity', 'unit_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'full_name',
        'total',
        'payment_method',
        'payment_status',
        'order_status',
        'created_at'
    )
    list_filter = ('payment_method', 'payment_status', 'order_status', 'created_at')
    search_fields = ('user__username', 'full_name', 'phone', 'address')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'book_title', 'quantity', 'unit_price')
    search_fields = ('book_title',)