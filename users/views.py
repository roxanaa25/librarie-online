from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator

from rest_framework import generics
from rest_framework.permissions import AllowAny

from books.models import Favorite
from orders.models import Order
from .serializers import RegisterSerializer


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Contul a fost creat pentru {username}! Te poți loga.')
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'users/register.html', {'form': form})


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@login_required
def profile(request):
    favorites_count = Favorite.objects.filter(user=request.user).count()

    return render(request, 'users/profile.html', {
        'favorites_count': favorites_count
    })


@login_required
def delete_account(request):
    if request.method == 'POST':
        active_orders = Order.objects.filter(
            user=request.user,
            order_status__in=['created', 'processing']
        )

        if active_orders.exists():
            messages.error(
                request,
                'Nu îți poți șterge contul deoarece ai comenzi active în procesare. '
                'Anulează comenzile active înainte de a șterge contul.'
            )
            return redirect('profile')

        request.user.delete()
        messages.success(request, 'Contul tău a fost șters definitiv.')
        return redirect('books:book_list')

    return render(request, 'users/delete_confirm.html')


@login_required
def favorite_list(request):
    favorite_list = Favorite.objects.filter(
        user=request.user
    ).select_related('book', 'book__category').order_by('-added_at')

    paginator = Paginator(favorite_list, 12)

    page_number = request.GET.get('page')
    favorites = paginator.get_page(page_number)

    return render(request, 'users/favorite_list.html', {
        'favorites': favorites
    })