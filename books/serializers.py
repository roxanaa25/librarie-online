from django.db.models import Avg, Count
from rest_framework import serializers
from .models import Book, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class BookSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'slug',
            'description',
            'price',
            'stock',
            'cover',
            'category',
            'available',
            'average_rating',
            'reviews_count'
        ]

    def get_average_rating(self, obj):
        value = getattr(obj, 'average_rating', None)

        if value is None:
            value = obj.reviews.filter(
                parent__isnull=True,
                approved=True
            ).aggregate(avg=Avg('rating'))['avg']

        if value is None:
            return 0

        return round(value, 1)

    def get_reviews_count(self, obj):
        value = getattr(obj, 'reviews_count', None)

        if value is None:
            value = obj.reviews.filter(
                parent__isnull=True,
                approved=True
            ).count()

        return value