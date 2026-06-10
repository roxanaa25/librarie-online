from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Count

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Book, Category, Favorite
from .serializers import BookSerializer, CategorySerializer


def book_list(request):
    book_list = Book.objects.filter(available=True).select_related('category').order_by('-created_at')
    paginator = Paginator(book_list, 12)

    page_number = request.GET.get('page')
    books = paginator.get_page(page_number)

    favorite_books = []

    if request.user.is_authenticated:
        favorite_books = list(
            Favorite.objects.filter(user=request.user).values_list('book_id', flat=True)
        )

    return render(
        request,
        'books/book_list.html',
        {
            'books': books,
            'favorite_books': favorite_books
        }
    )


def book_detail(request, slug):
    book = get_object_or_404(Book.objects.select_related('category'), slug=slug, available=True)

    is_favorite = False

    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(
            user=request.user,
            book=book
        ).exists()

    return render(request, 'books/book_detail.html', {
        'book': book,
        'is_favorite': is_favorite
    })


class BookPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class BookListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = BookSerializer
    pagination_class = BookPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return []

    def get_queryset(self):
        queryset = Book.objects.filter(available=True).select_related('category').annotate(
            average_rating=Avg(
                'reviews__rating',
                filter=Q(reviews__parent__isnull=True, reviews__approved=True)
            ),
            reviews_count=Count(
                'reviews',
                filter=Q(reviews__parent__isnull=True, reviews__approved=True),
                distinct=True
            )
        )

        query = self.request.query_params.get('q', '').strip()
        category_slug = self.request.query_params.get('category', '').strip()
        sort = self.request.query_params.get('sort', '').strip()
        min_price = self.request.query_params.get('min_price', '').strip()
        max_price = self.request.query_params.get('max_price', '').strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(description__icontains=query)
            )

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass

        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass

        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'title_asc':
            queryset = queryset.order_by('title')
        elif sort == 'title_desc':
            queryset = queryset.order_by('-title')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset.distinct()


class BookRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.select_related('category').annotate(
        average_rating=Avg(
            'reviews__rating',
            filter=Q(reviews__parent__isnull=True, reviews__approved=True)
        ),
        reviews_count=Count(
            'reviews',
            filter=Q(reviews__parent__isnull=True, reviews__approved=True),
            distinct=True
        )
    )
    serializer_class = BookSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return []


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer


@login_required
def toggle_favorite(request, slug):
    book = get_object_or_404(Book, slug=slug)

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        book=book
    )

    if not created:
        favorite.delete()

    page = request.GET.get('page', 1)

    return redirect(f'/?page={page}')


class FavoriteListAPIView(generics.ListAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        favorite_book_ids = Favorite.objects.filter(
            user=self.request.user
        ).values_list('book_id', flat=True)

        return Book.objects.filter(
            id__in=favorite_book_ids
        ).select_related('category')


class ToggleFavoriteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        book = get_object_or_404(Book, slug=slug)

        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            book=book
        )

        if created:
            return Response(
                {
                    'is_favorite': True,
                    'message': 'Cartea a fost adăugată la favorite.'
                },
                status=status.HTTP_201_CREATED
            )

        favorite.delete()

        return Response(
            {
                'is_favorite': False,
                'message': 'Cartea a fost eliminată de la favorite.'
            },
            status=status.HTTP_200_OK
        )