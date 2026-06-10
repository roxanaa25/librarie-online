from rest_framework import serializers
from .models import CartItem
from books.serializers import BookSerializer


class CartItemSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    item_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'book', 'quantity', 'item_total']

    def get_item_total(self, obj):
        return obj.total_price