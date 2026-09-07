from .models import AuditLog

def audit(*, user, action, model_name, description, store=None, object_id=None, metadata=None):
    if not getattr(user, "is_authenticated", False):
        return None
    return AuditLog.objects.create(
        user=user, store=store, action=action, model_name=model_name,
        object_id=object_id, description=description, metadata=metadata or {},
    )
