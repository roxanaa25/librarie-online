from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from books.models import Book


class Order(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Ramburs la livrare'),
        ('card', 'Card online'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'În așteptare'),
        ('paid', 'Plătită'),
        ('cancelled', 'Anulată'),
    ]

    ORDER_STATUS_CHOICES = [
        ('created', 'Creată'),
        ('processing', 'În procesare'),
        ('completed', 'Finalizată'),
        ('cancelled', 'Anulată'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('20.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='created')
    stock_updated = models.BooleanField(default=False)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Comandă'
        verbose_name_plural = 'Comenzi'

    def __str__(self):
        username = self.user.username if self.user else 'Utilizator șters'
        return f"Comanda #{self.id} - {username}"


class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True)
    book_title = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Produs comandat'
        verbose_name_plural = 'Produse comandate'

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.book_title} x {self.quantity}"