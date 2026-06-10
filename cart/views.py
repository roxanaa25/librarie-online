from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

from books.models import Book
from .models import CartItem
from .serializers import CartItemSerializer
from constants import SHIPPING_COST


def cart_detail(request):
    return render(request, 'cart/cart_detail.html')


class CartItemListAPIView(ListAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(
            user=self.request.user
        ).select_related('book', 'book__category')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        subtotal = sum(item.total_price for item in queryset)
        shipping = SHIPPING_COST if queryset.exists() else Decimal('0.00')
        total = subtotal + shipping

        return Response({
            'items': serializer.data,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
            'count': sum(item.quantity for item in queryset)
        })


class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        book_id = request.data.get('book_id')
        quantity = request.data.get('quantity', 1)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 1

        if quantity < 1:
            quantity = 1

        book = get_object_or_404(Book, id=book_id, available=True)

        if book.stock <= 0:
            return Response(
                {'message': 'Această carte nu mai este disponibilă în stoc.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item = CartItem.objects.filter(
            user=request.user,
            book=book
        ).first()

        existing_quantity = cart_item.quantity if cart_item else 0
        requested_total = existing_quantity + quantity

        if requested_total > book.stock:
            available_quantity = book.stock - existing_quantity

            if available_quantity <= 0:
                return Response(
                    {'message': 'Ai deja în coș cantitatea maximă disponibilă pentru această carte.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {'message': f'Nu poți adăuga această cantitate. Mai sunt disponibile doar {available_quantity} bucăți.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if cart_item:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                user=request.user,
                book=book,
                quantity=quantity
            )

        return Response({
            'message': 'Cartea a fost adăugată în coș.',
            'item_id': cart_item.id,
            'quantity': cart_item.quantity
        }, status=status.HTTP_201_CREATED)


class UpdateCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        quantity = request.data.get('quantity')

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {'message': 'Cantitatea introdusă nu este validă.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity < 1:
            return Response(
                {'message': 'Cantitatea trebuie să fie cel puțin 1.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity > cart_item.book.stock:
            return Response(
                {'message': f'Nu poți selecta această cantitate. În stoc sunt disponibile doar {cart_item.book.stock} bucăți.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        return Response({
            'message': 'Cantitatea a fost actualizată.',
            'quantity': cart_item.quantity
        })


class RemoveCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        cart_item.delete()

        return Response({
            'message': 'Produsul a fost șters din coș.'
        }, status=status.HTTP_200_OK)