from django.urls import path
from .views import (
    order_v, cart_v, add_to_cart, remove_from_cart, 
    checkout_v, clear_cart, order_detail_json_v, check_orders_status_v
)

urlpatterns = [
    path('orders/', order_v, name='order_v'),
    path('cart/', cart_v, name='cart_v'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('clear-cart/', clear_cart, name='clear_cart'),
    path('checkout/', checkout_v, name='checkout_v'),
    path('order-detail/<int:order_id>/', order_detail_json_v, name='order_detail_json'),
    path('check-orders-status/', check_orders_status_v, name='check_orders_status'),
]