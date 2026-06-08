from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.contrib import messages
from django.utils import timezone
from .models import LogNotificacion
from apps.subscriptions.models import Suscripcion
from apps.clients.models import HistorialCliente
from apps.accounts.models import RecordatorioTemplate


class LogNotificacionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LogNotificacion
    template_name = 'notifications/log_list.html'
    context_object_name = 'logs'
    paginate_by = 20
    permission_required = 'notifications.view_lognotificacion'


@login_required
@permission_required('notifications.add_lognotificacion', raise_exception=True)
def enviar_recordatorio_manual(request, suscripcion_id):
    suscripcion = get_object_or_404(Suscripcion, pk=suscripcion_id)
    cliente = suscripcion.cliente

    if LogNotificacion.objects.filter(suscripcion=suscripcion, canal=LogNotificacion.Canal.WHATSAPP).exists():
        messages.warning(request, f'Ya se envió un recordatorio de WhatsApp para esta suscripción.')
        return redirect('suscripcion_list')

    template = RecordatorioTemplate.get_active()
    if template:
        mensaje = template.render(
            cliente=cliente.nombre,
            plan=suscripcion.plan.nombre,
            vencimiento=suscripcion.fecha_vencimiento.strftime('%d/%m/%Y'),
            precio=f'${suscripcion.plan.precio:,.2f}',
        )
    else:
        mensaje = f'Hola {cliente.nombre}, tu suscripción {suscripcion.plan.nombre} vence el {suscripcion.fecha_vencimiento.strftime("%d/%m/%Y")}. ¡Renueva ahora!'

    try:
        import requests
        resp_wa = requests.post(
            settings.WHATSAPP_API_URL,
            json={'number': cliente.telefono, 'message': mensaje},
            timeout=10,
        )
        wa_ok = resp_wa.ok
        wa_resp = resp_wa.text[:500]
    except Exception as e:
        wa_ok = False
        wa_resp = str(e)

    LogNotificacion.objects.create(
        cliente=cliente,
        suscripcion=suscripcion,
        canal=LogNotificacion.Canal.WHATSAPP,
        destinatario=cliente.telefono,
        mensaje=mensaje,
        enviado_ok=wa_ok,
        respuesta_api=wa_resp,
    )

    if cliente.email:
        try:
            resp_email = requests.post(
                'https://api.resend.com/emails',
                headers={'Authorization': 'Bearer re_placeholder', 'Content-Type': 'application/json'},
                json={
                    'from': 'notificaciones@tudominio.com',
                    'to': cliente.email,
                    'subject': 'Recordatorio de vencimiento',
                    'text': mensaje,
                },
                timeout=10,
            )
            email_ok = resp_email.ok
            email_resp = resp_email.text[:500]
        except Exception as e:
            email_ok = False
            email_resp = str(e)

        LogNotificacion.objects.create(
            cliente=cliente,
            suscripcion=suscripcion,
            canal=LogNotificacion.Canal.EMAIL,
            destinatario=cliente.email,
            mensaje=mensaje,
            enviado_ok=email_ok,
            respuesta_api=email_resp,
        )

    HistorialCliente.objects.create(
        cliente=cliente,
        usuario=request.user,
        cambio=f'Recordatorio enviado manualmente por {request.user.get_full_name() or request.user.username}'
    )

    if wa_ok:
        messages.success(request, f'Recordatorio enviado a {cliente.nombre}.')
    else:
        messages.error(request, f'Error al enviar WhatsApp a {cliente.nombre}: {wa_resp}')

    return redirect('suscripcion_list')
