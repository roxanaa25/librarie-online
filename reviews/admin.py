from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'rating', 'parent', 'approved', 'created_at')
    list_filter = ('rating', 'approved', 'created_at')
    search_fields = ('user__username', 'book__title', 'comment')