from django.urls import path

from .views import users_v, register_v, about_v, contact_v, forgot_password, products_v

urlpatterns = [
    path('', users_v, name='user_login'),
    path('register/', register_v, name='user_register'),
    path('products/', products_v, name='products'),
    path('about/', about_v, name='about'),
    path('contact/', contact_v, name='contact'),
    path('forgot-password/', forgot_password, name='forgot_password'),
]