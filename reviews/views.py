from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from books.models import Book
from .models import Review
from .serializers import ReviewSerializer


class BookReviewAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, slug):
        book = get_object_or_404(Book, slug=slug, available=True)

        reviews = Review.objects.filter(
            book=book,
            parent__isnull=True,
            approved=True
        ).select_related('user').prefetch_related('replies__user').order_by('-created_at')

        serializer = ReviewSerializer(
            reviews,
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)

    def post(self, request, slug):
        book = get_object_or_404(Book, slug=slug, available=True)

        comment = request.data.get('comment', '').strip()
        rating = request.data.get('rating')
        parent_id = request.data.get('parent_id')

        if not comment:
            return Response(
                {'message': 'Comentariul nu poate fi gol.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if parent_id:
            if not request.user.is_staff:
                return Response(
                    {'message': 'Doar administratorul poate răspunde la recenzii.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            parent_review = get_object_or_404(
                Review,
                id=parent_id,
                book=book,
                parent__isnull=True,
                approved=True
            )

            reply = Review.objects.create(
                user=request.user,
                book=book,
                parent=parent_review,
                comment=comment,
                approved=True
            )

            serializer = ReviewSerializer(
                reply,
                context={'request': request}
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if Review.objects.filter(
            user=request.user,
            book=book,
            parent__isnull=True
        ).exists():
            return Response(
                {'message': 'Ai adăugat deja o recenzie pentru această carte.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return Response(
                {'message': 'Ratingul trebuie să fie un număr între 1 și 5.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if rating < 1 or rating > 5:
            return Response(
                {'message': 'Ratingul trebuie să fie între 1 și 5 stele.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        review = Review.objects.create(
            user=request.user,
            book=book,
            rating=rating,
            comment=comment,
            approved=False
        )

        serializer = ReviewSerializer(
            review,
            context={'request': request}
        )

        return Response(
            {'message': 'Recenzia ta a fost trimisă și urmează să fie aprobată.'},
            status=status.HTTP_201_CREATED
        )


class ReviewDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, review_id):
        review = get_object_or_404(
            Review,
            id=review_id,
            user=request.user,
            parent__isnull=True
        )

        comment = request.data.get('comment', '').strip()
        rating = request.data.get('rating')

        if not comment:
            return Response(
                {'message': 'Comentariul nu poate fi gol.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return Response(
                {'message': 'Ratingul trebuie să fie un număr între 1 și 5.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if rating < 1 or rating > 5:
            return Response(
                {'message': 'Ratingul trebuie să fie între 1 și 5 stele.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        review.comment = comment
        review.rating = rating
        review.approved = False
        review.save()

        serializer = ReviewSerializer(
            review,
            context={'request': request}
        )

        return Response(
            {'message': 'Recenzia a fost actualizată și urmează să fie aprobată din nou.'},
            status=status.HTTP_200_OK
        )

    def delete(self, request, review_id):
        review = get_object_or_404(
            Review,
            id=review_id,
            user=request.user,
            parent__isnull=True
        )

        review.delete()

        return Response(
            {'message': 'Recenzia a fost ștearsă cu succes.'},
            status=status.HTTP_200_OK
        )