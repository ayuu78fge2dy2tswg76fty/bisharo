from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from .models import AuditLog, _thread_locals
import json
from django.core.serializers.json import DjangoJSONEncoder

# List of models we want to track
# We can dynamically track everything or specific ones. 
# For now, let's track everything in specific apps or explicit imports.
# Ideally, we connect to specific sender models or all.
# Let's track 'ordersapp.Order', 'productapp.Product' for now as requested.
# But connecting to ALL models might be too noisy. 
# Let's start with a generic receiver and filter by app_label.

CHANGES_BUFFER = {}

def get_current_user():
    return getattr(_thread_locals, 'user', None)

@receiver(pre_save)
def capture_old_state(sender, instance, **kwargs):
    # Filter only for relevant apps
    if sender._meta.app_label not in ['ordersapp', 'productapp', 'usersapp']:
        return

    # Skip AuditLog itself
    if sender == AuditLog:
        return

    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            # Create a dictionary of the old state
            # We exclude fields that are not relevant or binary
            old_data = model_to_dict(old_instance)
            CHANGES_BUFFER[instance.pk] = old_data
        except sender.DoesNotExist:
            CHANGES_BUFFER[instance.pk] = {}
    else:
        CHANGES_BUFFER[instance.pk] = {}

@receiver(post_save)
def log_save_change(sender, instance, created, **kwargs):
    if sender._meta.app_label not in ['ordersapp', 'productapp', 'usersapp']:
        return
    if sender == AuditLog:
        return

    user = get_current_user()
    
    # If no user (e.g. system task), we can still log it as 'System' or store None
    # effectively handled by nullable FK

    action = 'CREATE' if created else 'UPDATE'
    changes = {}

    if created:
        # For create, strictly speaking new values
        try:
            changes = model_to_dict(instance)
        except:
            pass
    else:
        # Compare with buffer
        old_data = CHANGES_BUFFER.get(instance.pk, {})
        new_data = model_to_dict(instance)
        
        for key, new_val in new_data.items():
            old_val = old_data.get(key)
            if old_val != new_val:
                # Basic comparison suitable for primitives
                # For complex fields like Dates, might need string conversion
                changes[key] = {'old': str(old_val), 'new': str(new_val)}
        
        # Cleanup buffer
        if instance.pk in CHANGES_BUFFER:
            del CHANGES_BUFFER[instance.pk]

    if not changes and not created:
        return 

    # Serialize changes safely
    try:
        changes_json = json.loads(json.dumps(changes, cls=DjangoJSONEncoder))
    except:
        changes_json = {"error": "Could not serialize changes"}

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        model_name=sender.__name__,
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        changes=changes_json
    )

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender._meta.app_label not in ['ordersapp', 'productapp', 'usersapp']:
        return
    if sender == AuditLog:
        return

    user = get_current_user()
    
    # Serialize the full object state
    try:
        deleted_data = model_to_dict(instance)
        changes_json = json.loads(json.dumps(deleted_data, cls=DjangoJSONEncoder))
    except:
        changes_json = {'info': 'Object deleted', 'error': 'Could not serialize deleted data'}

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action='DELETE',
        model_name=sender.__name__,
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        changes=changes_json
    )
