from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .decorators import admin_required, permission_required, super_admin_required
from usersapp.models import userka
from productapp.models import Product
from ordersapp.models import Order
from django.db.models import Count, Sum, F
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt

def admin_login(request):
    # This view is now largely redundant due to coreapp gateway, 
    # but keeping it for direct access if needed.
    if request.session.get('admin_id'):
        admin = get_object_or_404(User, id=request.session['admin_id'])
        if admin.is_superuser:
            return redirect('admin_analytics')
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            request.session['admin_id'] = user.id
            request.session['admin_name'] = user.get_full_name() or user.username
            messages.success(request, f"Welcome, {request.session['admin_name']}!")
            if user.is_superuser:
                return redirect('admin_analytics')
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid admin credentials.")
            
    return render(request, 'adminapp/login.html')

def admin_logout(request):
    if 'admin_id' in request.session:
        del request.session['admin_id']
    if 'admin_name' in request.session:
        del request.session['admin_name']
    messages.success(request, "Logged out successfully.")
    return redirect('user_login')

@super_admin_required
def admin_analytics(request):
    admin = get_object_or_404(User, id=request.session['admin_id'])
    
    # 1. Assets / Inventory
    total_products = Product.objects.count()
    low_stock_threshold = 10
    low_stock_products = Product.objects.filter(quatentity__gt=0, quatentity__lt=low_stock_threshold)
    out_of_stock_products = Product.objects.filter(quatentity=0)
    
    # 2. Sales & Transactions
    delivered_orders = Order.objects.filter(status='delivered')
    total_revenue = delivered_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_transactions = Order.objects.exclude(status='canceled').count()
    
    # 3. User Statistics
    total_customers = userka.objects.count()
    total_admins = User.objects.filter(is_staff=True).count()
    
    # 4. Financial Overview (Expenses and Net Profit removed as per request)
    total_expenses = 0
    net_profit = total_revenue
    
    # Best-selling products (Top 5)
    # This requires reaching through OrderItem to Product and summing quantity.
    from ordersapp.models import OrderItem
    best_sellers = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).filter(total_sold__gt=0).order_by('-total_sold')[:5]
    
    # Products not selling
    not_selling = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).filter(total_sold__isnull=True)[:5]
    
    # 4. Graphs & Statistics (Last 30 days daily sales)
    today = timezone.now().date()
    last_30_days = [(today - timedelta(days=i)) for i in range(29, -1, -1)]
    
    daily_sales = []
    daily_labels = []
    
    for day in last_30_days:
        daily_labels.append(day.strftime('%b %d'))
        day_revenue = delivered_orders.filter(order_date__date=day).aggregate(Sum('total_price'))['total_price__sum'] or 0
        daily_sales.append(float(day_revenue))
    
    # Category Distribution (Pie Chart)
    from catogories.models import Category
    category_data = Category.objects.annotate(count=Count('products')).values('name', 'count')
    
    context = {
        'admin': admin,
        'inventory': {
            'total': total_products,
            'low_stock': low_stock_products,
            'out_of_stock': out_of_stock_products,
        },
        'finances': {
            'revenue': total_revenue,
            'expenses': total_expenses,
            'profit': net_profit,
        },
        'sales': {
            'transactions': total_transactions,
            'best_sellers': best_sellers,
            'not_selling': not_selling,
            'total_customers': total_customers,
            'total_admins': total_admins,
        },
        'charts': {
            'labels': daily_labels,
            'sales_data': daily_sales,
            'category_labels': [c['name'] for c in category_data],
            'category_counts': [c['count'] for c in category_data],
        },
        'title': 'Analytics Dashboard'
    }
    return render(request, 'adminapp/analyze.html', context)

@admin_required
def admin_dashboard(request):
    admin = get_object_or_404(User, id=request.session['admin_id'])
    
    # Dashboard Statistics
    stats = {
        'total_users': userka.objects.count(),
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'delivered_orders': Order.objects.filter(status='delivered').count(),
    }
    
    # Recent Orders
    recent_orders = Order.objects.all().order_by('-order_date')[:5]
    
    context = {
        'admin': admin,
        'stats': stats,
        'recent_orders': recent_orders,
    }
    return render(request, 'adminapp/dashboard.html', context)

# Category Management
@permission_required('can_manage_products')
def category_list(request):
    from catogories.models import Category
    admin = User.objects.get(id=request.session['admin_id'])
    query = request.GET.get('q', '')
    categories = Category.objects.all().order_by('-created_at')
    
    if query:
        categories = categories.filter(name__icontains=query)

    return render(request, 'adminapp/categories/list.html', {
        'categories': categories,
        'query': query,
        'admin': admin
    })

@permission_required('can_manage_products')
def category_add(request):
    from catogories.models import Category
    admin = get_object_or_404(User, id=request.session['admin_id'])
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        Category.objects.create(name=name, description=description)
        messages.success(request, "Category created successfully.")
        return redirect('admin_category_list')
    return render(request, 'adminapp/categories/form.html', {'category': None, 'title': 'Add Category', 'admin': admin})

@permission_required('can_manage_products')
def category_edit(request, id):
    from catogories.models import Category
    admin = get_object_or_404(User, id=request.session['admin_id'])
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.save()
        messages.success(request, "Category updated successfully.")
        return redirect('admin_category_list')
    return render(request, 'adminapp/categories/form.html', {'category': category, 'title': 'Edit Category', 'admin': admin})

@permission_required('can_manage_products')
def category_delete(request, id):
    from catogories.models import Category
    # Security check
    admin = get_object_or_404(User, id=request.session['admin_id'])
    if not admin.is_superuser:
        messages.error(request, "Only Super Admins have access to delete.")
        return redirect('admin_category_list')
        
    category = get_object_or_404(Category, id=id)
    category.delete()
    messages.success(request, "Category deleted successfully.")
    return redirect('admin_category_list')

# Product Management
@permission_required('can_manage_products')
def product_list(request):
    from productapp.models import Product
    admin = User.objects.get(id=request.session['admin_id'])
    query = request.GET.get('q', '')
    products = Product.objects.all().order_by('-created_at')
    
    if query:
        products = products.filter(name__icontains=query) | products.filter(description__icontains=query)

    return render(request, 'adminapp/products/list.html', {
        'products': products,
        'query': query,
        'admin': admin
    })

@permission_required('can_manage_products')
def product_add(request):
    from productapp.models import Product
    from catogories.models import Category
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        available = request.POST.get('available') == 'on'
        
        category = get_object_or_404(Category, id=category_id)
        
        Product.objects.create(
            name=name, price=price, quatentity=quantity,
            description=description, category=category,
            image=image, available=available
        )
        messages.success(request, "Product added successfully.")
        return redirect('admin_product_list')
        
    admin = get_object_or_404(User, id=request.session['admin_id'])
    return render(request, 'adminapp/products/form.html', {'product': None, 'categories': categories, 'title': 'Add Product', 'admin': admin})

@permission_required('can_manage_products')
def product_edit(request, id):
    from productapp.models import Product
    from catogories.models import Category
    product = get_object_or_404(Product, id=id)
    categories = Category.objects.all()
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.quatentity = request.POST.get('quantity')
        product.description = request.POST.get('description')
        product.available = request.POST.get('available') == 'on'
        
        category_id = request.POST.get('category')
        product.category = get_object_or_404(Category, id=category_id)
        
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            
        product.save()
        messages.success(request, "Product updated successfully.")
        return redirect('admin_product_list')
    
    admin = get_object_or_404(User, id=request.session['admin_id'])
    return render(request, 'adminapp/products/form.html', {'product': product, 'categories': categories, 'title': 'Edit Product', 'admin': admin})

@permission_required('can_manage_products')
def product_delete(request, id):
    from productapp.models import Product
    # Security check
    admin = get_object_or_404(User, id=request.session['admin_id'])
    if not admin.is_superuser:
        messages.error(request, "Only Super Admins have access to delete.")
        return redirect('admin_product_list')

    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect('admin_product_list')

# Order Management
@permission_required('can_manage_orders')
def order_list(request):
    from ordersapp.models import Order
    admin = User.objects.get(id=request.session['admin_id'])
    status_filter = request.GET.get('status')
    query = request.GET.get('q', '')
    
    # Prefetch items and product to avoid N+1 queries when showing images
    orders = Order.objects.all().prefetch_related('items__product').order_by('-order_date')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
        
    if query:
        # Search by order ID, username, customer name, or phone
        if query.isdigit():
             orders = orders.filter(id=query) | orders.filter(phone_number__icontains=query)
        else:
             orders = orders.filter(user__username__icontains=query) | orders.filter(user__name__icontains=query) | orders.filter(phone_number__icontains=query)

    # Annotate/Attach first item image for the list view
    # We do this in python to keep it simple, or we could use Subquery but that's complex for images.
    # Since we paginated usually (but here we don't yet), iterating over all might be heavy if thousands.
    # For now, let's just rely on the template accessing 'order.items.first.product.image.url' safely.
    # The prefetch_related above optimizes the db hits.
        
    return render(request, 'adminapp/orders/list.html', {
        'orders': orders, 
        'current_status': status_filter,
        'query': query,
        'admin': admin
    })

@permission_required('can_manage_orders')
def order_status_update(request, id, status):
    from django.core.mail import send_mail
    from django.conf import settings
    order = get_object_or_404(Order, id=id)
    
    valid_statuses = ['pending', 'shipped', 'delivered', 'canceled']
    if status in valid_statuses:
        # Trigger stock reduction if status is 'shipped' and not previously deducted
        # (Note: Stock logic was consolidated/fixed earlier, ensuring here we trigger email)
        
        if status == 'shipped':
            # 1. Stock Deduction Logic (if needed explicitly here or relying on model method call previously discussed)
            # Retaining previous logic if present, or just adding email. Assuming previous logic was removed by user edit, re-adding minimal safety check if needed, but focusing on email.
            
            # 2. Email Notification
            if order.email:
                subject = f"Your Order #{order.id} has been Shipped! - Gado Store"
                message = f"Hello {order.user.name},\n\nGreat news! Your order #{order.id} has been processed and is now SHIPPED.\n\nIt is on its way to you.\n\nThank you for shopping with Gado Store!"
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [order.email]
                
                try:
                    send_mail(subject, message, email_from, recipient_list)
                    messages.success(request, f"Email notification sent to {order.email}")
                except Exception as e:
                    messages.warning(request, f"Order shipped but failed to send email: {str(e)}")

        order.status = status
        order.save()
        messages.success(request, f"Order #{id} status updated to {status.capitalize()}.")
    else:
        messages.error(request, "Invalid status transition.")
        
    return redirect('admin_order_list')

@permission_required('can_manage_orders')
def order_delete(request, id):
    from ordersapp.models import Order
    order = get_object_or_404(Order, id=id)
    
    # Check if admin has delete permission
    admin = get_object_or_404(User, id=request.session['admin_id'])
    if not admin.is_superuser:
        messages.error(request, "Only Super Admins have access to delete.")
        return redirect('admin_order_list')
        
    order.delete()
    messages.success(request, f"Order #{id} deleted successfully.")
    return redirect('admin_order_list')

# Store User Management
@permission_required('can_manage_users')
def admin_user_list(request):
    from usersapp.models import userka
    admin = User.objects.get(id=request.session['admin_id'])
    query = request.GET.get('q', '')
    users = userka.objects.all().order_by('-created_at')
    
    if query:
        users = users.filter(name__icontains=query) | users.filter(username__icontains=query) | users.filter(email__icontains=query)
        
    return render(request, 'adminapp/users/list.html', {
        'users': users, 
        'query': query,
        'admin': admin
    })

@permission_required('can_manage_users')
def admin_user_delete(request, id):
    from usersapp.models import userka
    # Check permission
    admin = get_object_or_404(User, id=request.session['admin_id'])
    if not admin.is_superuser:
        messages.error(request, "Only Super Admins have access to delete.")
        return redirect('admin_user_list')
        
    user = get_object_or_404(userka, id=id)
    user.delete()
    messages.success(request, f"User {user.username} has been removed.")
    return redirect('admin_user_list')

# Admin Staff Management

@super_admin_required
def admin_list(request):
    admin = get_object_or_404(User, id=request.session['admin_id'])
    admins = User.objects.filter(is_staff=True).order_by('-date_joined')
    return render(request, 'adminapp/staff/list.html', {'admins': admins, 'admin': admin})

@super_admin_required
def admin_add(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        is_super = request.POST.get('is_super_admin') == 'on'
        
        # Max 3 Super Admins Check
        if is_super and User.objects.filter(is_superuser=True).count() >= 3:
             messages.error(request, "Maximum of 3 Super Admins allowed. Please downgrade an existing one first.")
             admin = get_object_or_404(User, id=request.session['admin_id'])
             return render(request, 'adminapp/staff/form.html', {'staff': None, 'title': 'Add Staff Member', 'admin': admin})

        # Split fullname if possible
        names = fullname.split(' ', 1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else ""

        user = User.objects.create_user(
            username=username, 
            password=password, 
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=is_super
        )
        messages.success(request, "Admin account created.")
        return redirect('admin_member_list')
    
    admin = get_object_or_404(User, id=request.session['admin_id'])
    return render(request, 'adminapp/staff/form.html', {'staff': None, 'title': 'Add Staff Member', 'admin': admin})

@super_admin_required
def admin_edit(request, id):
    admin_obj = get_object_or_404(User, id=id, is_staff=True)
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        names = fullname.split(' ', 1)
        admin_obj.first_name = names[0]
        admin_obj.last_name = names[1] if len(names) > 1 else ""
        
        admin_obj.username = request.POST.get('username')
        admin_obj.email = request.POST.get('email')
        if request.POST.get('password'):
            admin_obj.set_password(request.POST.get('password'))
            
        # Max 3 Super Admins Check
        new_is_super = request.POST.get('is_super_admin') == 'on'
        if new_is_super and not admin_obj.is_superuser:
            if User.objects.filter(is_superuser=True).count() >= 3:
                 messages.error(request, "Maximum of 3 Super Admins allowed.")
                 # preserve other changes or just return
                 return redirect('admin_member_edit', id=id)

        admin_obj.is_superuser = new_is_super
        admin_obj.save()
        messages.success(request, "Admin account updated.")
        return redirect('admin_member_list')
    # Add a pseudo fullname for the template if it expects 'fullname'
    admin_obj.fullname = f"{admin_obj.first_name} {admin_obj.last_name}".strip() or admin_obj.username
    
    admin = get_object_or_404(User, id=request.session['admin_id'])
    return render(request, 'adminapp/staff/form.html', {'staff': admin_obj, 'title': 'Edit Staff Member', 'admin': admin})

@super_admin_required
def admin_delete(request, id):
    admin = get_object_or_404(User, id=request.session['admin_id'])
    
    if request.method == 'POST':
        # 1. Password Verification
        password = request.POST.get('password')
        if not admin.check_password(password):
            messages.error(request, "Incorrect password. Deletion cancelled.")
            return redirect('admin_member_list')

        # 2. Self Deletion Check
        if int(id) == int(admin.id):
            messages.error(request, "You cannot delete your own account.")
            return redirect('admin_member_list')
        
        target_admin = get_object_or_404(User, id=id)

        # 3. Last Super Admin Protection
        if target_admin.is_superuser:
            super_count = User.objects.filter(is_superuser=True).count()
            if super_count <= 1:
                messages.error(request, "First before you delete super admin add must be have at least anather 1 super admin.")
                return redirect('admin_member_list')
        
        target_admin.delete()
        messages.success(request, f"Admin {target_admin.username} removed successfully.")
        return redirect('admin_member_list')
    
    # If GET, just redirect (deletion must be POST)
    return redirect('admin_member_list')

# API for Detail Modals
@admin_required
def product_detail_api(request, id):
    product = get_object_or_404(Product, id=id)
    data = {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': str(product.price),
        'quantity': product.quatentity,
        'category': product.category.name,
        'image': product.image.url if product.image else None,
        'available': product.available,
        'created_at': product.created_at.strftime('%Y-%m-%d %H:%M')
    }
    return JsonResponse(data)

@admin_required
def order_detail_api(request, id):
    order = get_object_or_404(Order, id=id)
    items = []
    for item in order.items.all():
        items.append({
            'product': item.product.name,
            'quantity': item.quantity,
            'price': str(item.price_at_order),
            'total': str(item.get_total_price()),
            'image': item.product.image.url if item.product.image else '/static/img/no-image.png'
        })
    
    data = {
        'id': order.id,
        'customer': order.user.name,
        'username': order.user.username,
        'email': order.email,
        'phone': order.phone_number,
        'address': order.address,
        'date': order.order_date.strftime('%Y-%m-%d %H:%M'),
        'total': str(order.total_price),
        'status': order.status,
        'items': items
    }
    return JsonResponse(data)

@admin_required
def customer_detail_api(request, id):
    user = get_object_or_404(userka, id=id)
    
    # Calculate Statistics
    total_orders = user.orders.count()
    total_spent = user.orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    pending_orders = user.orders.filter(status='pending').count()
    last_order = user.orders.order_by('-order_date').first()
    
    data = {
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email,
        'phone': user.phone_number or 'Not provided',
        'address': user.address or 'No address on file',
        'gender': user.get_gender_display() if hasattr(user, 'get_gender_display') else user.gender,
        'image': user.profile_picture.url if user.profile_picture else None,
        'joined_at': user.created_at.strftime('%Y-%m-%d %H:%M'),
        # Stats
        'total_orders': total_orders,
        'total_spent': str(total_spent),
        'pending_orders': pending_orders,
        'last_order': last_order.order_date.strftime('%Y-%m-%d %H:%M') if last_order else 'None',
        'gender_value': user.gender  # Raw value for edit form
    }

    # Add password for superuser
    admin_id = request.session.get('admin_id')
    if admin_id:
        admin_obj = User.objects.filter(id=admin_id).first()
        if admin_obj and admin_obj.is_superuser:
            data['password'] = user.password

    return JsonResponse(data)

@csrf_exempt
@super_admin_required
def customer_update_api(request, id):
    if request.method == 'POST':
        try:
            user = get_object_or_404(userka, id=id)
            
            # Update fields
            user.name = request.POST.get('name')
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.phone_number = request.POST.get('phone')
            user.gender = request.POST.get('gender')
            user.address = request.POST.get('address')
            user.password = request.POST.get('password')
            
            # Handle profile picture if provided
            if 'image' in request.FILES:
                user.profile_picture = request.FILES['image']
                
            user.save()
            return JsonResponse({'success': True, 'message': 'User updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@admin_required
def category_detail_api(request, id):
    from catogories.models import Category
    category = get_object_or_404(Category, id=id)
    products = []
    
    try:
        # Get products using related_name 'products' safely
        product_list = getattr(category, 'products', None)
        if product_list is None:
            product_list = getattr(category, 'product_set', None)
        
        if product_list is not None:
            product_list = product_list.all()
        else:
            product_list = []
        
        for product in product_list:
            products.append({
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'quantity': product.quatentity,
                'image': product.image.url if product.image else None,
                'available': product.available
            })
        
        data = {
            'id': category.id,
            'name': category.name,
            'description': category.description or 'No description provided.',
            'created_at': category.created_at.strftime('%Y-%m-%d %H:%M') if category.created_at else 'N/A',
            'product_count': len(products),
            'products': products
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
from django.core.paginator import Paginator
from .models import AuditLog

@super_admin_required
def admin_audit_log(request):
    admin = get_object_or_404(User, id=request.session['admin_id'])
    log_list = AuditLog.objects.all()
    paginator = Paginator(log_list, 50) # Show 50 logs per page
    
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    return render(request, 'adminapp/audit/log.html', {'logs': logs, 'admin': admin})

@super_admin_required
def audit_log_delete(request, id):
    log = get_object_or_404(AuditLog, id=id)
    log.delete()
    messages.success(request, 'Log entry deleted successfully.')
    return redirect('admin_audit_log')

@super_admin_required
def audit_log_detail_api(request, id):
    try:
        log = get_object_or_404(AuditLog, id=id)
        
        user_info = 'System'
        user_role = 'System'
        user_email = 'N/A'
        
        if log.user:
            user_info = f"{log.user.username}"
            if log.user.get_full_name():
                user_info += f" ({log.user.get_full_name()})"
            
            user_email = log.user.email
            user_role = 'Super Admin' if log.user.is_superuser else 'Staff Member'

        data = {
            'id': log.id,
            'user': user_info,
            'user_email': user_email,
            'user_role': user_role,
            'action': log.action,
            'model': log.model_name,
            'object': log.object_repr,
            'object_id': log.object_id,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'changes': log.changes
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
