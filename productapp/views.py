from django.shortcuts import render
from .models import Product
from catogories.models import Category
from django.db.models import Q

def product_v(request):
    # Get filter parameters
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort = request.GET.get('sort', 'latest')

    # Initial Queryset
    alaab = Product.objects.all()

    # Apply Search
    if query:
        alaab = alaab.filter(
            Q(name__icontains=query) | 
            Q(category__name__icontains=query) |
            Q(description__icontains=query)
        )

    # Apply Category Filter
    if category_id:
        alaab = alaab.filter(category_id=category_id)

    # Apply Price Filter
    if min_price:
        try:
            alaab = alaab.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            alaab = alaab.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Apply Sorting
    if sort == 'price_low':
        alaab = alaab.order_by('price')
    elif sort == 'price_high':
        alaab = alaab.order_by('-price')
    else: # latest
        alaab = alaab.order_by('-created_at')

    # Get all categories for filter dropdown
    categories = Category.objects.all()

    db = {
        'alaab': alaab,
        'categories': categories,
        'query': query,
        'category_id': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort
    }
    return render(request, 'productapp/products.html', db)

def product_detail(request, id):
    product = Product.objects.get(id=id)
    db = {
        'productdetail': product
    }
    return render(request, 'productapp/productdet.html', db)
