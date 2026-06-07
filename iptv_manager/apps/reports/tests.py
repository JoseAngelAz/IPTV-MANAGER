from io import BytesIO
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

from apps.clients.models import Cliente
from apps.finance.models import MovimientoFinanciero
from apps.notifications.models import LogNotificacion
from apps.subscriptions.models import Plan, Suscripcion
from .models import ReportTemplate
from .report_pdf import generate_report_pdf
from .report_excel import generate_report_excel

User = get_user_model()


class ReportTemplateTest(TestCase):
    def test_presets_return_three_templates(self):
        presets = ReportTemplate.get_presets()
        self.assertEqual(len(presets), 3)
        self.assertIn(1, presets)
        self.assertIn(2, presets)
        self.assertIn(3, presets)

    def test_preset_names(self):
        presets = ReportTemplate.get_presets()
        self.assertEqual(presets[1].nombre, 'Ejecutivo')
        self.assertEqual(presets[2].nombre, 'Moderno')
        self.assertEqual(presets[3].nombre, 'Clásico')

    def test_report_str(self):
        t = ReportTemplate(nombre='Test')
        self.assertEqual(str(t), 'Test')


class ReportAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
        self.user = User.objects.create_user('user', 'user@test.com', 'pass')

    def test_redirect_anonymous(self):
        r = self.client.get(reverse('reports:report_create'))
        self.assertEqual(r.status_code, 302)

    def test_block_non_superuser(self):
        self.client.force_login(self.user, backend='django.contrib.auth.backends.ModelBackend')
        r = self.client.get(reverse('reports:report_create'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/dashboard/', r.url)

    def test_allow_superuser(self):
        self.client.force_login(self.admin, backend='django.contrib.auth.backends.ModelBackend')
        r = self.client.get(reverse('reports:report_create'))
        self.assertEqual(r.status_code, 200)

    def test_requires_at_least_one_section(self):
        self.client.force_login(self.admin, backend='django.contrib.auth.backends.ModelBackend')
        r = self.client.post(reverse('reports:report_create'), {})
        self.assertRedirects(r, reverse('reports:report_create'))


class ReportDataCollectionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
        self.client.force_login(self.admin, backend='django.contrib.auth.backends.ModelBackend')

        self.cliente = Cliente.objects.create(
            nombre='Test Cliente', telefono='123456789',
            email='test@test.com', dispositivo_id='AA:BB:CC:DD:EE:FF'
        )
        self.plan = Plan.objects.create(nombre='Plan Básico', precio=10, duracion_dias=30)
        self.suscripcion = Suscripcion.objects.create(
            cliente=self.cliente, plan=self.plan,
            fecha_inicio=timezone.now(), fecha_vencimiento=timezone.now() + timezone.timedelta(days=30)
        )
        MovimientoFinanciero.objects.create(
            tipo='ingreso', monto=100,
            descripcion='Pago test', suscripcion=self.suscripcion
        )
        LogNotificacion.objects.create(
            cliente=self.cliente, suscripcion=self.suscripcion,
            canal='whatsapp', destinatario='123456789',
            mensaje='Test', enviado_ok=True
        )

    def test_preview_with_clients(self):
        r = self.client.post(reverse('reports:report_create'), {
            'clientes': 'on', 'action': 'preview', 'template_id': 1,
            'date_start': '', 'date_end': '',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Test Cliente')

    def test_preview_with_finanzas(self):
        r = self.client.post(reverse('reports:report_create'), {
            'finanzas': 'on', 'action': 'preview', 'template_id': 2,
            'date_start': '', 'date_end': '',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Ingreso')

    def test_preview_with_notificaciones(self):
        r = self.client.post(reverse('reports:report_create'), {
            'notificaciones': 'on', 'action': 'preview', 'template_id': 3,
            'date_start': '', 'date_end': '',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'WhatsApp')

    def test_preview_with_suscripciones(self):
        r = self.client.post(reverse('reports:report_create'), {
            'suscripciones': 'on', 'action': 'preview', 'template_id': 2,
            'date_start': '', 'date_end': '',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Test Cliente')
        self.assertContains(r, 'Plan Básico')
        self.assertContains(r, 'Activo')

    def test_preview_all_sections(self):
        r = self.client.post(reverse('reports:report_create'), {
            'clientes': 'on', 'finanzas': 'on', 'notificaciones': 'on', 'suscripciones': 'on',
            'action': 'preview', 'template_id': 1,
            'date_start': '', 'date_end': '',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Test Cliente')
        self.assertContains(r, 'Ingreso')
        self.assertContains(r, 'WhatsApp')
        self.assertContains(r, 'Plan Básico')
        self.assertContains(r, 'Activo')

    def test_download_pdf(self):
        r = self.client.post(reverse('reports:report_create'), {
            'clientes': 'on', 'action': 'download', 'template_id': 1,
            'format': 'pdf', 'date_start': '', 'date_end': '',
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=', r['Content-Disposition'])

    def test_download_excel(self):
        r = self.client.post(reverse('reports:report_create'), {
            'clientes': 'on', 'action': 'download', 'template_id': 1,
            'format': 'excel', 'date_start': '', 'date_end': '',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheet', r['Content-Type'])
        self.assertIn('attachment; filename=', r['Content-Disposition'])

    def test_preview_each_template_renders(self):
        for tid in [1, 2, 3]:
            r = self.client.post(reverse('reports:report_create'), {
                'clientes': 'on', 'action': 'preview', 'template_id': tid,
                'date_start': '', 'date_end': '',
            })
            self.assertEqual(r.status_code, 200, f'Template {tid} failed')

    def test_download_pdf_each_template(self):
        for tid in [1, 2, 3]:
            r = self.client.post(reverse('reports:report_create'), {
                'clientes': 'on', 'action': 'download', 'template_id': tid,
                'format': 'pdf', 'date_start': '', 'date_end': '',
            })
            self.assertEqual(r.status_code, 200, f'PDF template {tid} failed')

    def test_date_filtering(self):
        today = date.today()
        r = self.client.post(reverse('reports:report_create'), {
            'clientes': 'on', 'action': 'preview', 'template_id': 1,
            'date_start': today.isoformat(), 'date_end': today.isoformat(),
        })
        self.assertEqual(r.status_code, 200)


class PDFGenerationUnitTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')

    def test_generate_pdf_no_data(self):
        buf = generate_report_pdf(1, ['clientes'], {}, None, None, self.admin)
        self.assertIsInstance(buf, BytesIO)
        self.assertGreater(buf.getbuffer().nbytes, 500)

    def test_generate_pdf_modern_template(self):
        data = {'clientes': [{'nombre': 'Juan', 'telefono': '123', 'email': 'j@t.com',
                              'dispositivo_id': 'AA:BB', 'fecha_registro': '2025-01-01'}]}
        buf = generate_report_pdf(2, ['clientes'], data, None, None, self.admin)
        self.assertGreater(buf.getbuffer().nbytes, 500)

    def test_generate_pdf_clasico_template(self):
        data = {'finanzas': [{'tipo': 'ingreso', 'monto': 100, 'fecha': '2025-01-01', 'descripcion': 'Pago'}],
                'resumen_finanzas': {'ingresos': 100, 'egresos': 0, 'neto': 100}}
        buf = generate_report_pdf(3, ['finanzas'], data, None, None, self.admin)
        self.assertGreater(buf.getbuffer().nbytes, 500)

    def test_generate_pdf_all_sections(self):
        data = {
            'clientes': [{'nombre': 'Juan', 'telefono': '123', 'email': 'j@t.com',
                          'dispositivo_id': 'AA:BB', 'fecha_registro': '2025-01-01'}],
            'finanzas': [{'tipo': 'ingreso', 'monto': 100, 'fecha': '2025-01-01', 'descripcion': 'Pago'}],
            'resumen_finanzas': {'ingresos': 100, 'egresos': 0, 'neto': 100},
            'notificaciones': [{'canal': 'WhatsApp', 'destinatario': '123', 'cliente_nombre': 'Juan',
                                'enviado_ok': True, 'fecha_creacion': '2025-01-01T10:00:00'}],
            'suscripciones': [{'cliente_nombre': 'Juan', 'plan_nombre': 'Básico', 'plan_precio': 10,
                               'fecha_inicio': '2025-01-01', 'fecha_vencimiento': '2025-01-31',
                               'estado': 'Activo'}],
        }
        for tid in [1, 2, 3]:
            buf = generate_report_pdf(tid, ['clientes', 'finanzas', 'notificaciones', 'suscripciones'],
                                       data, None, None, self.admin)
            self.assertGreater(buf.getbuffer().nbytes, 500, f'Template {tid} generated small PDF')


class ExcelGenerationUnitTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')

    def test_generate_excel(self):
        data = {
            'clientes': [{'nombre': 'Juan', 'telefono': '123', 'email': 'j@t.com',
                          'dispositivo_id': 'AA:BB', 'fecha_registro': '2025-01-01'}],
            'finanzas': [{'tipo': 'ingreso', 'monto': 100, 'fecha': '2025-01-01', 'descripcion': 'Pago'}],
            'resumen_finanzas': {'ingresos': 100, 'egresos': 0, 'neto': 100},
            'notificaciones': [{'canal': 'WhatsApp', 'destinatario': '123', 'cliente_nombre': 'Juan',
                                'enviado_ok': True, 'fecha_creacion': '2025-01-01'}],
            'suscripciones': [{'cliente_nombre': 'Juan', 'plan_nombre': 'Básico', 'plan_precio': 10,
                               'fecha_inicio': '2025-01-01', 'fecha_vencimiento': '2025-01-31',
                               'estado': 'Activo'}],
        }
        buf = generate_report_excel(['clientes', 'finanzas', 'notificaciones', 'suscripciones'],
                                     data, None, None, self.admin)
        self.assertGreater(buf.getbuffer().nbytes, 500)

    def test_generate_excel_empty(self):
        buf = generate_report_excel(['clientes'], {}, None, None, self.admin)
        self.assertGreater(buf.getbuffer().nbytes, 500)
