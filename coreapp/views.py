from django.shortcuts import render,redirect
from django.contrib import messages

# Create your views here.
from usersapp.models import userka
from productapp.models import Product
from django.db.models import Q

# Login required decorator for regular users
def user_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.warning(request, 'Fadlan gal si aad u aragto boggan.')
            return redirect('user_login')
        return view_func(request, *args, **kwargs)
    return wrapper

from catogories.models import Category
def products_v(request):
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()

    # Search
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    # Filter by Category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    context = {
        'products': products,
        'categories': categories,
        'search_query': query, # Pass back to template to keep in input
        'selected_category': int(category_id) if category_id else None
    }
    return render(request, 'coreapp/product.html', context)

def users_v(request):
    # Auto-redirection removed to ensure landing page is always accessible if navigated to directly.
    # Sessions are still checked inside the login logic if needed.

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 1. First, check if it's an Admin trying to login
        from django.contrib.auth import authenticate
        from django.contrib.auth.models import User
        
        admin_user = authenticate(request, username=username, password=password)
        if admin_user is not None and (admin_user.is_staff or admin_user.is_superuser):
            request.session['admin_id'] = admin_user.id
            request.session['admin_name'] = admin_user.get_full_name() or admin_user.username
            messages.success(request, f"Welcome back, Administrator {request.session['admin_name']}!")
            if admin_user.is_superuser:
                return redirect('admin_analytics')
            else:
                return redirect('admin_dashboard')

        # 2. If not admin, check if it's a regular Customer
        try:
            usr = userka.objects.get(
                Q(username=username) | 
                Q(email=username) | 
                Q(phone_number=username),
                password=password
            )
            request.session['user_id'] = usr.id
            request.session['user_name'] = usr.username
            request.session['user_email'] = usr.email
            messages.success(request, f"Welcome back, {usr.name}!")
            return redirect('user_home')
        except userka.DoesNotExist:
            products = Product.objects.filter(available=True).order_by('-created_at')[:4]
            return render(request, 'coreapp/logincore.html', {
                'error': 'Magaca isticmaalaha ama lambarka sirta ah waa qalad. Fadlan isku day markale.',
                'products': products
            })
    
    products = Product.objects.filter(available=True).order_by('-created_at')[:4]
    return render(request, 'coreapp/logincore.html', {'products': products})

def register_v(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        gender = request.POST.get('gender')
        
        if userka.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'coreapp/logincore.html', {'show_register': True})
        
        if userka.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'coreapp/logincore.html', {'show_register': True})
            
        new_user = userka.objects.create(
            name=name,
            username=username,
            email=email,
            password=password,
            gender=gender
        )
        
        # Auto-login the user
        request.session['user_id'] = new_user.id
        request.session['user_name'] = new_user.username
        request.session['user_email'] = new_user.email
        
        messages.success(request, f"Registration successful! Welcome, {new_user.name}.")
        return redirect('user_home')
        
    return render(request, 'coreapp/logincore.html', {'show_register': True})

def about_v(request):
    return render(request, 'coreapp/about.html')

def contact_v(request):
    return render(request, 'coreapp/contect.html')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = userka.objects.get(email=email)
            return JsonResponse({
                'success': True,
                'password': user.password
            })
        except userka.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Emailkan majiro'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})