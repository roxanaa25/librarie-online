from django.db import models
from django.contrib.auth.models import User
from books.models import Book


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-added_at']

    @property
    def total_price(self):
        return self.book.price * self.quantity

    def __str__(self):
        return f"{self.user.username} - {self.book.title} x {self.quantity}"