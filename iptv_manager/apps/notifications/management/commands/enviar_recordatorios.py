from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.subscriptions.models import Suscripcion
from apps.notifications.models import LogNotificacion
from apps.clients.models import HistorialCliente


class Command(BaseCommand):
    help = 'Envía recordatorios a suscripciones que vencen en exactamente 3 días'

    def handle(self, *args, **options):
        hoy = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target = hoy + timezone.timedelta(days=3)

        suscripciones = Suscripcion.objects.filter(
            estado=Suscripcion.Estado.ACTIVO,
            fecha_vencimiento__date=target.date(),
        ).select_related('cliente', 'plan')

        if not suscripciones.exists():
            self.stdout.write(self.style.WARNING(f'No hay suscripciones por vencer el {target.date()}'))
            return

        import requests

        for suscripcion in suscripciones:
            cliente = suscripcion.cliente
            mensaje = (
                f'Hola {cliente.nombre}, tu suscripción {suscripcion.plan.nombre} '
                f'vence el {suscripcion.fecha_vencimiento.strftime("%d/%m/%Y")}. '
                f'¡Renueva ahora para no perder el servicio!'
            )

            if not LogNotificacion.objects.filter(
                suscripcion=suscripcion, canal=LogNotificacion.Canal.WHATSAPP
            ).exists() and cliente.telefono:
                try:
                    resp = requests.post(
                        settings.WHATSAPP_API_URL,
                        json={'number': cliente.telefono, 'message': mensaje},
                        timeout=10,
                    )
                    wa_ok = resp.ok
                    wa_resp = resp.text[:500]
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

                status = 'OK' if wa_ok else 'FALLO'
                self.stdout.write(f'[WhatsApp][{status}] {cliente.nombre} — {cliente.telefono}')

            if not LogNotificacion.objects.filter(
                suscripcion=suscripcion, canal=LogNotificacion.Canal.EMAIL
            ).exists() and cliente.email:
                try:
                    resp = requests.post(
                        'https://api.resend.com/emails',
                        headers={
                            'Authorization': 'Bearer re_placeholder',
                            'Content-Type': 'application/json',
                        },
                        json={
                            'from': 'notificaciones@tudominio.com',
                            'to': cliente.email,
                            'subject': 'Recordatorio de vencimiento',
                            'text': mensaje,
                        },
                        timeout=10,
                    )
                    email_ok = resp.ok
                    email_resp = resp.text[:500]
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

                status = 'OK' if email_ok else 'FALLO'
                self.stdout.write(f'[Email][{status}] {cliente.nombre} — {cliente.email}')

            HistorialCliente.objects.create(
                cliente=cliente,
                usuario=None,
                cambio=f'Recordatorio automático enviado (vence {suscripcion.fecha_vencimiento.strftime("%d/%m/%Y")})'
            )

        self.stdout.write(self.style.SUCCESS(f'Procesadas {suscripciones.count()} suscripciones'))
