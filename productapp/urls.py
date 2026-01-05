from django.urls import path

from .views import product_v, product_detail


urlpatterns = [
    path('products/', product_v, name='product_list'),
    path('products/<int:id>/', product_detail, name='product_detail'),
]