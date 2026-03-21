from core.models import ActivityLog


def log_activity(*, user=None, action, obj=None, metadata=None):
    """
    Persist a normalized audit log entry.

    When `obj` is provided, the log stores the affected model label and primary key.
    """

    object_type = ''
    object_id = None
    if obj is not None:
        object_type = obj._meta.label_lower
        object_id = obj.pk

    return ActivityLog.objects.create(
        user=user,
        action=action,
        object_type=object_type,
        object_id=object_id,
        metadata=metadata or {},
    )
