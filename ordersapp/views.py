from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse

# Create your views here.

from .models import Order, OrderItem
from productapp.models import Product
from usersapp.models import userka

def order_v(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('user_login')
    orders = Order.objects.filter(user_id=user_id)[:4]
    return render(request, 'ordersapp/orders.html', {'orders': orders})

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    messages.success(request, "Item added to cart!")
    return redirect('product_list')

def cart_v(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('user_login')
    return render(request, 'ordersapp/cart.html')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
    return redirect('cart_v')

def clear_cart(request):
    request.session['cart'] = {}
    return redirect('cart_v')

def checkout_v(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('user_login')
        
    user = get_object_or_404(userka, id=user_id)
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('product_list')

    if request.method == 'POST':
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        payment_method = request.POST.get('payment_method', 'cash')
        
        order = Order.objects.create(
            user=user,
            phone_number=phone,
            address=address,
            email=user.email,
            payment_method=payment_method
        )
        
        total_price = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            total_price += product.price * int(quantity)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_order=product.price
            )
            
        order.total_price = total_price
        order.save()
            
        request.session['cart'] = {}
        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_v')
        
    return render(request, 'ordersapp/checkout.html', {'user': user})

def order_detail_json_v(request, order_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    order = get_object_or_404(Order, id=order_id, user_id=user_id)
    items = []
    for item in order.items.all():
        items.append({
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.price_at_order),
            'total': float(item.get_total_price()),
            'image_url': item.product.image.url if item.product.image else None
        })
        
    data = {
        'id': order.id,
        'items': items,
        'total_price': float(order.total_price),
        'status': order.status,
        'status_display': order.get_status_display(),
        'order_date': order.order_date.strftime("%d %b, %Y"),
        'address': order.address,
        'phone': order.phone_number
    }
    return JsonResponse(data)

def check_orders_status_v(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    orders = Order.objects.filter(user_id=user_id).values('id', 'status')
    status_map = dict(Order.STATUS_CHOICES)
    
    order_data = []
    for o in orders:
        order_data.append({
            'id': o['id'],
            'status': o['status'],
            'status_display': status_map.get(o['status'], o['status'])
        })
        
    return JsonResponse({'orders': order_data})

