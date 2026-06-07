from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.conf import settings

from apps.clients.models import Cliente
from apps.finance.models import MovimientoFinanciero
from apps.notifications.models import LogNotificacion
from apps.subscriptions.models import Suscripcion
from .report_pdf import generate_report_pdf
from .report_excel import generate_report_excel
from .models import ReportTemplate

SECTIONS = ['clientes', 'finanzas', 'notificaciones', 'suscripciones']


def _collect_data(sections, date_start, date_end):
    data = {}

    if 'clientes' in sections:
        qs = Cliente.objects.annotate(
            subs_activas=Count('suscripciones', filter=Q(suscripciones__estado='activo')),
            total_gastado=Sum('suscripciones__plan__precio', filter=Q(suscripciones__estado__in=['activo', 'vencido'])),
        )
        if date_start and date_end:
            qs = qs.filter(fecha_registro__date__gte=date_start, fecha_registro__date__lte=date_end)
        data['clientes'] = list(qs.values('nombre', 'telefono', 'email', 'dispositivo_id', 'fecha_registro', 'subs_activas', 'total_gastado'))

    if 'finanzas' in sections:
        qs = MovimientoFinanciero.objects.all()
        if date_start and date_end:
            qs = qs.filter(fecha__date__gte=date_start, fecha__date__lte=date_end)
        movs = qs.values('tipo', 'monto', 'fecha', 'descripcion')
        data['finanzas'] = list(movs)
        ingresos = sum(m['monto'] for m in movs if m.get('tipo') == 'ingreso')
        egresos = sum(abs(m['monto']) for m in movs if m.get('tipo') == 'egreso')
        data['resumen_finanzas'] = {
            'ingresos': float(ingresos),
            'egresos': float(egresos),
            'neto': float(ingresos - egresos),
        }

    if 'notificaciones' in sections:
        qs = LogNotificacion.objects.select_related('cliente')
        if date_start and date_end:
            qs = qs.filter(fecha_envio__date__gte=date_start, fecha_envio__date__lte=date_end)
        notifs = []
        for n in qs:
            notifs.append({
                'canal': n.get_canal_display(),
                'destinatario': n.destinatario,
                'cliente_nombre': n.cliente.nombre if n.cliente else '—',
                'enviado_ok': n.enviado_ok,
                'fecha_creacion': n.fecha_envio,
                'mensaje': (n.mensaje[:80] + '…') if n.mensaje and len(n.mensaje) > 80 else (n.mensaje or ''),
            })
        data['notificaciones'] = notifs

    if 'suscripciones' in sections:
        qs = Suscripcion.objects.select_related('cliente', 'plan')
        if date_start and date_end:
            qs = qs.filter(fecha_inicio__date__gte=date_start, fecha_inicio__date__lte=date_end)
        subs = []
        for s in qs:
            dias_restantes = (s.fecha_vencimiento - timezone.now()).days if s.fecha_vencimiento else 0
            subs.append({
                'cliente_nombre': s.cliente.nombre if s.cliente else '—',
                'cliente_telefono': s.cliente.telefono if s.cliente else '',
                'plan_nombre': s.plan.nombre if s.plan else '—',
                'plan_precio': float(s.plan.precio) if s.plan else 0,
                'plan_duracion': s.plan.duracion_dias if s.plan else 0,
                'fecha_inicio': s.fecha_inicio,
                'fecha_vencimiento': s.fecha_vencimiento,
                'dias_restantes': max(dias_restantes, 0),
                'estado': s.get_estado_display(),
            })
        data['suscripciones'] = subs

    return data


@login_required
def report_create(request):
    if not request.user.is_superuser:
        messages.error(request, 'Solo el administrador maestro puede generar reportes.')
        return redirect('dashboard')

    sections = SECTIONS
    templates = ReportTemplate.get_presets()

    if request.method == 'POST':
        selected_sections = [s for s in sections if request.POST.get(s) == 'on']
        if not selected_sections:
            messages.warning(request, 'Selecciona al menos una sección para el reporte.')
            return redirect('reports:report_create')

        template_id = int(request.POST.get('template_id', 1))
        date_start = request.POST.get('date_start', '') or None
        date_end = request.POST.get('date_end', '') or None
        action = request.POST.get('action', 'preview')
        format_type = request.POST.get('format', 'pdf')
        report_margin = request.POST.get('report_margin', 'normal')
        report_font = request.POST.get('report_font', 'helvetica')
        report_padding = request.POST.get('report_padding', 'normal')
        report_landscape = request.POST.get('report_landscape') == 'on'
        report_chart = request.POST.get('report_chart', 'bar')

        data = _collect_data(selected_sections, date_start, date_end)

        if action == 'preview' or format_type == 'jpg':
            ctx = {
                'sections': selected_sections,
                'data': data,
                'date_start': date_start,
                'date_end': date_end,
                'template_id': template_id,
                'user': request.user,
                'template': templates.get(template_id),
                'now': datetime.now(),
            }
            html = render_to_string('reports/preview.html', ctx, request=request)
            return render(request, 'reports/preview.html', {
                **ctx, 'html_content': html
            })

        if format_type == 'pdf':
            buf = generate_report_pdf(template_id, selected_sections, data, date_start, date_end, request.user,
                                      margin=report_margin, font=report_font, padding=report_padding,
                                      landscape_mode=report_landscape, chart_type=report_chart)
            filename = f'reporte_{"_".join(selected_sections)}_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
            response = HttpResponse(buf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            buf = generate_report_excel(selected_sections, data, date_start, date_end, request.user)
            filename = f'reporte_{"_".join(selected_sections)}_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
            response = HttpResponse(buf,
                                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

    return render(request, 'reports/report_create.html', {
        'sections': sections,
        'templates': templates,
        'today': timezone.now().date(),
    })
