#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating default groups..."
python manage.py shell <<EOF
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.clients.models import Cliente, HistorialCliente
from apps.subscriptions.models import Plan, Suscripcion
from apps.finance.models import MovimientoFinanciero
from apps.notifications.models import LogNotificacion
from apps.accounts.models import UserActivityLog

superadmin, _ = Group.objects.get_or_create(name='Superadmin')
manager, _ = Group.objects.get_or_create(name='Gerente')
soporte, _ = Group.objects.get_or_create(name='Soporte')

for model in [Cliente, HistorialCliente, Plan, Suscripcion, MovimientoFinanciero, LogNotificacion, UserActivityLog]:
    ct = ContentType.objects.get_for_model(model)
    perms = Permission.objects.filter(content_type=ct)
    manager.permissions.add(*perms)

for model in [UserActivityLog, LogNotificacion]:
    ct = ContentType.objects.get_for_model(model)
    for perm in Permission.objects.filter(content_type=ct, codename__startswith='view_'):
        soporte.permissions.add(perm)

for model in [Cliente, Suscripcion]:
    ct = ContentType.objects.get_for_model(model)
    for perm in Permission.objects.filter(content_type=ct):
        if perm.codename.startswith('view_') or perm.codename.startswith('add_') or perm.codename.startswith('change_'):
            soporte.permissions.add(perm)

ct = ContentType.objects.get_for_model(MovimientoFinanciero)
for perm in Permission.objects.filter(content_type=ct, codename__startswith='view_'):
    soporte.permissions.add(perm)

for model in [Cliente, Suscripcion]:
    ct = ContentType.objects.get_for_model(model)
    for perm in Permission.objects.filter(content_type=ct, codename__startswith='delete_'):
        manager.permissions.remove(perm)
        soporte.permissions.remove(perm)
EOF

echo "Setup complete. Starting application..."

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
