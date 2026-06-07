import threading
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SessionConfig

_thread_locals = threading.local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    return getattr(_thread_locals, 'request', None)


def set_current_user(user):
    _thread_locals.user = user


def set_current_request(request):
    _thread_locals.request = request


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        set_current_user(request.user if request.user.is_authenticated else None)
        if request.user.is_authenticated:
            try:
                cfg = SessionConfig.get_config()
                request.session.set_expiry(cfg.timeout_minutes * 60)
            except Exception:
                pass
        response = self.get_response(request)
        set_current_user(None)
        set_current_request(None)
        return response


@receiver(post_save)
def log_model_save(sender, instance, created, raw, **kwargs):
    if raw:
        return
    from apps.accounts.models import UserActivityLog, User
    from django.contrib.sessions.models import Session
    skip_models = (UserActivityLog, User, Session)
    if sender in skip_models:
        return
    model_name = sender._meta.verbose_name or sender.__name__
    action = 'create' if created else 'update'
    user = get_current_user()
    request = get_current_request()
    if not user or not user.is_authenticated:
        return
    try:
        object_id = int(instance.pk) if instance.pk is not None else None
    except (ValueError, TypeError):
        object_id = None
    UserActivityLog.objects.create(
        user=user,
        username=user.username,
        action=action,
        model_name=model_name,
        object_repr=str(instance)[:255],
        object_id=object_id,
        details=f'{action.capitalize()} de {model_name}',
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        path=request.path if request else '',
    )


@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    from apps.accounts.models import UserActivityLog, User
    from django.contrib.sessions.models import Session
    if sender in (UserActivityLog, User, Session):
        return
    model_name = sender._meta.verbose_name or sender.__name__
    user = get_current_user()
    request = get_current_request()
    if not user or not user.is_authenticated:
        return
    try:
        object_id = int(instance.pk) if instance.pk is not None else None
    except (ValueError, TypeError):
        object_id = None
    UserActivityLog.objects.create(
        user=user,
        username=user.username,
        action='delete',
        model_name=model_name,
        object_repr=str(instance)[:255],
        object_id=object_id,
        details=f'Eliminación de {model_name}',
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        path=request.path if request else '',
    )
