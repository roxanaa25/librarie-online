from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'book_title',
            'quantity',
            'unit_price',
            'total_price',
            'cover'
        ]

    def get_total_price(self, obj):
        return obj.total_price

    def get_cover(self, obj):
        if obj.book and obj.book.cover:
            return obj.book.cover
        return None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    created_at = serializers.SerializerMethodField()
    payment_method_display = serializers.SerializerMethodField()
    payment_status_display = serializers.SerializerMethodField()
    order_status_display = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'full_name',
            'phone',
            'address',
            'city',
            'county',
            'postal_code',
            'subtotal',
            'shipping_cost',
            'total',
            'payment_method',
            'payment_method_display',
            'payment_status',
            'payment_status_display',
            'order_status',
            'order_status_display',
            'created_at',
            'items'
        ]

    def get_created_at(self, obj):
        luni = {
            1: 'ianuarie', 2: 'februarie', 3: 'martie',
            4: 'aprilie', 5: 'mai', 6: 'iunie',
            7: 'iulie', 8: 'august', 9: 'septembrie',
            10: 'octombrie', 11: 'noiembrie', 12: 'decembrie'
        }
        luna = luni[obj.created_at.month]
        return f"{obj.created_at.day} {luna} {obj.created_at.year}, {obj.created_at.strftime('%H:%M')}"

    def get_payment_method_display(self, obj):
        return obj.get_payment_method_display()

    def get_payment_status_display(self, obj):
        return obj.get_payment_status_display()

    def get_order_status_display(self, obj):
        return obj.get_order_status_display()