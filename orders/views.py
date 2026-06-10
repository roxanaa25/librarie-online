from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from cart.models import CartItem
from .models import Order, OrderItem
from .serializers import OrderSerializer
from constants import SHIPPING_COST


def calculate_cart_totals(cart_items):
    subtotal = sum(item.total_price for item in cart_items)
    shipping = SHIPPING_COST if cart_items.exists() else Decimal('0.00')
    total = subtotal + shipping
    return subtotal, shipping, total


def create_order_items(order, cart_items):
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            book=item.book,
            book_title=item.book.title,
            quantity=item.quantity,
            unit_price=item.book.price
        )


def validate_cart_stock(cart_items):
    for item in cart_items:
        if item.quantity > item.book.stock:
            return f'Cartea „{item.book.title}" nu are suficient stoc. Disponibil: {item.book.stock}.'
    return None


def decrease_order_stock(order):
    if order.stock_updated:
        return

    for item in order.items.select_related('book').all():
        if item.book:
            item.book.stock = max(item.book.stock - item.quantity, 0)
            item.book.save(update_fields=['stock'])

    order.stock_updated = True
    order.save(update_fields=['stock_updated'])


def restore_order_stock(order):
    if not order.stock_updated:
        return

    for item in order.items.select_related('book').all():
        if item.book:
            item.book.stock += item.quantity
            item.book.save(update_fields=['stock'])

    order.stock_updated = False
    order.save(update_fields=['stock_updated'])


@login_required
def checkout_page(request):
    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related('book', 'book__category')

    if not cart_items.exists():
        return redirect('cart:cart_detail')

    subtotal, shipping, total = calculate_cart_totals(cart_items)

    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
    })


class CreateCheckoutSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart_items = CartItem.objects.filter(
            user=request.user
        ).select_related('book', 'book__category')

        if not cart_items.exists():
            return Response(
                {'message': 'Coșul este gol.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stock_error = validate_cart_stock(cart_items)

        if stock_error:
            return Response(
                {'message': stock_error},
                status=status.HTTP_400_BAD_REQUEST
            )

        full_name = request.data.get('full_name', '').strip()
        phone = request.data.get('phone', '').strip()
        address = request.data.get('address', '').strip()
        city = request.data.get('city', '').strip()
        county = request.data.get('county', '').strip()
        postal_code = request.data.get('postal_code', '').strip()
        payment_method = request.data.get('payment_method', '').strip()

        if not full_name or not phone or not address or not city or not county:
            return Response(
                {'message': 'Completează toate câmpurile obligatorii.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if payment_method not in ['cash', 'card']:
            return Response(
                {'message': 'Metoda de plată nu este validă.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subtotal, shipping, total = calculate_cart_totals(cart_items)

        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            city=city,
            county=county,
            postal_code=postal_code,
            subtotal=subtotal,
            shipping_cost=shipping,
            total=total,
            payment_method=payment_method,
            payment_status='pending',
            order_status='created'
        )

        create_order_items(order, cart_items)

        if payment_method == 'cash':
            order.payment_status = 'pending'
            order.order_status = 'processing'
            order.save()

            decrease_order_stock(order)
            cart_items.delete()

            return Response({
                'message': 'Comanda a fost plasată cu succes.',
                'redirect_url': reverse('orders:order_success', args=[order.id])
            }, status=status.HTTP_201_CREATED)

        stripe.api_key = settings.STRIPE_SECRET_KEY

        line_items = []

        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': 'ron',
                    'product_data': {
                        'name': item.book.title,
                    },
                    'unit_amount': int(item.book.price * 100),
                },
                'quantity': item.quantity,
            })

        if shipping > 0:
            line_items.append({
                'price_data': {
                    'currency': 'ron',
                    'product_data': {
                        'name': 'Transport standard',
                    },
                    'unit_amount': int(shipping * 100),
                },
                'quantity': 1,
            })

        success_url = request.build_absolute_uri(
            reverse('orders:stripe_success')
        ) + '?session_id={CHECKOUT_SESSION_ID}'

        cancel_url = request.build_absolute_uri(
            reverse('orders:stripe_cancel')
        ) + f'?order_id={order.id}'

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='payment',
                line_items=line_items,
                customer_email=request.user.email if request.user.email else None,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'order_id': str(order.id),
                    'user_id': str(request.user.id)
                }
            )

            order.stripe_checkout_session_id = checkout_session.id
            order.save()

            return Response({
                'checkout_url': checkout_session.url
            }, status=status.HTTP_201_CREATED)

        except Exception as error:
            order.payment_status = 'cancelled'
            order.order_status = 'cancelled'
            order.save()

            return Response(
                {'message': 'A apărut o eroare la procesarea plății. Te rugăm să încerci din nou.'},
                status=status.HTTP_400_BAD_REQUEST
            )


@login_required
def stripe_success(request):
    session_id = request.GET.get('session_id')

    if not session_id:
        return redirect('cart:cart_detail')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    order = get_object_or_404(
        Order,
        stripe_checkout_session_id=session_id,
        user=request.user
    )

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception:
        return render(request, 'orders/success.html', {'order': order})

    try:
        payment_status = session['payment_status']
    except Exception:
        payment_status = None

    try:
        payment_intent = session['payment_intent']
    except Exception:
        payment_intent = None

    if payment_status == 'paid':
        order.payment_status = 'paid'
        order.order_status = 'processing'

        if payment_intent:
            order.stripe_payment_intent_id = payment_intent

        order.save()
        decrease_order_stock(order)
        CartItem.objects.filter(user=request.user).delete()

    return render(request, 'orders/success.html', {'order': order})


@login_required
def stripe_cancel(request):
    order_id = request.GET.get('order_id')

    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order.payment_status = 'cancelled'
        order.order_status = 'cancelled'
        order.save()

    return render(request, 'orders/cancel.html')


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/success.html', {'order': order})


class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20


@login_required
def my_orders_page(request):
    return render(request, 'orders/my_orders.html')


@login_required
def order_detail_page(request, order_id):
    return render(request, 'orders/order_detail.html', {'order_id': order_id})


class OrderListAPIView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items').order_by('-created_at')


class OrderDetailAPIView(RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items')


class CancelOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user
        )

        if order.order_status == 'completed':
            return Response(
                {'message': 'Comanda finalizată nu mai poate fi anulată.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.order_status == 'cancelled':
            return Response(
                {'message': 'Comanda este deja anulată.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.order_status = 'cancelled'

        if order.payment_method == 'cash':
            order.payment_status = 'cancelled'

        order.save()
        restore_order_stock(order)

        if order.payment_method == 'card' and order.payment_status == 'paid':
            return Response({
                'message': 'Comanda a fost anulată în aplicație. Stocul a fost refăcut, dar refund-ul Stripe nu este implementat în această versiune.'
            })

        return Response({
            'message': 'Comanda a fost anulată cu succes.'
        })