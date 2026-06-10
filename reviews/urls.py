from django.urls import path
from .views import BookReviewAPIView, ReviewDetailAPIView

app_name = 'reviews'

urlpatterns = [
    path('api/books/<slug:slug>/reviews/', BookReviewAPIView.as_view(), name='book-reviews-api'),
    path('api/reviews/<int:review_id>/', ReviewDetailAPIView.as_view(), name='review-detail-api'),
]