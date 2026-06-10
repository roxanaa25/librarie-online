from django.db import models
from django.contrib.auth.models import User
from books.models import Book


class Review(models.Model):

    RATING_CHOICES = [
        (1, '1 stea'),
        (2, '2 stele'),
        (3, '3 stele'),
        (4, '4 stele'),
        (5, '5 stele'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    comment = models.TextField()
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Recenzie'
        verbose_name_plural = 'Recenzii'

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"