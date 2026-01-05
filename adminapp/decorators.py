from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.contrib.auth.models import User

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        admin_id = request.session.get('admin_id')
        if not admin_id:
            messages.error(request, "Please login as admin to access this page.")
            return redirect('user_login')
        
        try:
            admin = User.objects.get(id=admin_id)
            if admin.is_staff or admin.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Access denied. Admin privileges required.")
                return redirect('user_login')
        except User.DoesNotExist:
            request.session.flush()
            messages.error(request, "Invalid admin session.")
            return redirect('user_login')
    return _wrapped_view

def super_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        admin_id = request.session.get('admin_id')
        if not admin_id:
            return redirect('user_login')
        
        try:
            admin = User.objects.get(id=admin_id)
            if not admin.is_superuser:
                messages.error(request, "Access denied. Super Admin privileges required.")
                return redirect('admin_dashboard')
        except User.DoesNotExist:
            request.session.flush()
            return redirect('user_login')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def permission_required(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            admin_id = request.session.get('admin_id')
            if not admin_id:
                return redirect('user_login')
            
            try:
                admin = User.objects.get(id=admin_id, is_staff=True)
                if admin.is_superuser:
                    return view_func(request, *args, **kwargs)
                
                # Simplified: staff have access to management modules for now
                # Or you can check specific user permissions: if admin.has_perm(permission_name):
                return view_func(request, *args, **kwargs)
            except User.DoesNotExist:
                request.session.flush()
                return redirect('user_login')
                
        return _wrapped_view
    return decorator
