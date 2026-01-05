from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import userka
from ordersapp.models import Order, OrderItem
from django.db.models import Sum

# 

def logout_v(request):
    request.session.flush()
    return redirect('user_login')

def edit_profile_v(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('user_login')
        
    try:
        user = userka.objects.get(id=user_id)
    except userka.DoesNotExist:
        # Only remove user session data, preserve admin session if any
        if 'user_id' in request.session: del request.session['user_id']
        if 'user_name' in request.session: del request.session['user_name']
        if 'user_email' in request.session: del request.session['user_email']
        return redirect('user_login')
    
    if request.method == 'POST':
        user.name = request.POST.get('name')
        user.email = request.POST.get('email')
        user.phone_number = request.POST.get('phone')
        user.address = request.POST.get('address')
        
        # New Fields
        new_username = request.POST.get('username')
        new_password = request.POST.get('password')
        
        if new_username and new_username != user.username:
            if userka.objects.filter(username=new_username).exists():
                messages.error(request, "Username already taken!")
                return redirect('user_profile')
            user.username = new_username
            request.session['user_name'] = new_username # Update session
            
        if new_password:
            user.password = new_password
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
            
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('user_profile')
        
    return redirect('user_profile')

def home_v(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('user_login')
        
    try:
        db_user = userka.objects.get(id=user_id)
    except userka.DoesNotExist:
        if 'user_id' in request.session: del request.session['user_id']
        if 'user_name' in request.session: del request.session['user_name']
        if 'user_email' in request.session: del request.session['user_email']
        return redirect('user_login')
    
    # Live Stats
    user_orders = Order.objects.filter(user=db_user)
    active_orders_count = user_orders.filter(status__in=['pending', 'shipped']).count()
    total_spent = user_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_items_bought = OrderItem.objects.filter(order__user=db_user).aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    # Recent Activity (Last 5 orders)
    recent_activity = user_orders.order_by('-order_date')[:5]
    
    db = {
        'user': db_user,
        'active_orders_count': active_orders_count,
        'total_spent': total_spent,
        'total_items_bought': total_items_bought,
        'recent_activity': recent_activity
    }
    return render(request, 'usersapp/home.html', db)

def profile_v(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('user_login')
    try:
        db_user = userka.objects.get(id=user_id)
    except userka.DoesNotExist:
        if 'user_id' in request.session: del request.session['user_id']
        if 'user_name' in request.session: del request.session['user_name']
        if 'user_email' in request.session: del request.session['user_email']
        return redirect('user_login')
    db = {
        'user': db_user
    }
    return render(request, 'usersapp/profile.html', db)