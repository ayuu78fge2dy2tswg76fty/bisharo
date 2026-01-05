from productapp.models import Product

def cart_processor(request):
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())
    
    cart_items = []
    total_cart_price = 0
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            item_total = product.price * quantity
            total_cart_price += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': item_total
            })
        except Product.DoesNotExist:
            continue
            
    return {
        'cart_count': cart_count,
        'cart_items': cart_items,
        'total_cart_price': total_cart_price
    }
