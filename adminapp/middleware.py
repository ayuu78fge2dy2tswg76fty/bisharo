import threading
from django.utils.deprecation import MiddlewareMixin

# We can re-use the thread local from models.py or define it here.
# To avoid circular imports if models imports this, let's keep the storage here 
# and have models import logic from here, OR keep it simple.
# Given the previous step defined logic in models.py, let's consolidate.
# Actually, for clean separation, middleware should set the thread local.

from django.contrib.auth.models import User
from .models import _thread_locals

class GlobalRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _thread_locals.request = request
        
        # Default to standard request.user
        _thread_locals.user = getattr(request, 'user', None)
        
        # If request.user is not the intended admin (e.g. system thinks it's superuser but session says staff)
        # or if request.user is not authenticated but session has admin_id (legacy login)
        admin_id = request.session.get('admin_id')
        if admin_id:
            try:
                # Manually fetch the user from the session ID for logging purposes
                # This ensures the Audit Log attributes the action to the actual Staff member
                # even if Django's auth system sees someone else (or no one).
                # We prioritize the session admin for audit logging context.
                actual_user = User.objects.get(id=admin_id)
                _thread_locals.user = actual_user
            except User.DoesNotExist:
                pass

    def process_response(self, request, response):
        # Cleanup to prevent memory leaks in long-running processes
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
        return response
