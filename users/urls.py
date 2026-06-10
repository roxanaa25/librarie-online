# users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views # Importăm tot din views pentru a accesa și funcția register și clasa RegisterAPIView
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('api/register/', views.RegisterAPIView.as_view(), name='api-register'),

    path('profile/', views.profile, name='profile'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('delete/', views.delete_account, name='delete_account'),

    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='users/password_change.html',
        success_url='/users/profile/'
    ), name='password_change'),
]