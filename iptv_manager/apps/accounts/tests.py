from decimal import Decimal
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import User, ThemeSettings, UserActivityLog, log_user_action, Tarea
from .middleware import set_current_user
from apps.clients.models import Cliente
from apps.subscriptions.models import Plan, Suscripcion
from apps.finance.models import MovimientoFinanciero


@override_settings(AXES_ENABLED=False, SECURE_SSL_REDIRECT=False)
class BaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.master = User.objects.create_superuser(
            username='master', password='master123', email='master@test.com'
        )
        self.admin_user = User.objects.create_user(
            username='admin2', password='admin123', first_name='Admin2'
        )
        self.soporte_user = User.objects.create_user(
            username='soporte1', password='soporte123', first_name='Soporte'
        )

        soporte_group = Group.objects.create(name='Soporte')
        gerente_group = Group.objects.create(name='Gerente')
        superadmin_group = Group.objects.create(name='Superadmin')

        for model in [Cliente, Suscripcion, Plan, MovimientoFinanciero]:
            ct = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=ct)
            gerente_group.permissions.add(*perms)

        for model in [Cliente, Suscripcion]:
            ct = ContentType.objects.get_for_model(model)
            for perm in Permission.objects.filter(content_type=ct):
                if perm.codename.startswith(('view_', 'add_', 'change_')):
                    soporte_group.permissions.add(perm)

        ct = ContentType.objects.get_for_model(MovimientoFinanciero)
        for perm in Permission.objects.filter(content_type=ct, codename__startswith='view_'):
            soporte_group.permissions.add(perm)

        self.admin_user.groups.add(gerente_group)
        self.soporte_user.groups.add(soporte_group)

        self.client_master = Client()
        self.client_master.force_login(self.master, backend='django.contrib.auth.backends.ModelBackend')
        self.client_admin = Client()
        self.client_admin.force_login(self.admin_user, backend='django.contrib.auth.backends.ModelBackend')
        self.client_soporte = Client()
        self.client_soporte.force_login(self.soporte_user, backend='django.contrib.auth.backends.ModelBackend')

        self.plan = Plan.objects.create(nombre='Premium', precio=299.99, duracion_dias=30)

    def tearDown(self):
        UserActivityLog.objects.all().delete()


class UserModelTest(BaseTest):
    def test_profile_picture_field_exists(self):
        field = User._meta.get_field('profile_picture')
        self.assertTrue(field)

    def test_user_str(self):
        u = User(username='testuser', first_name='Test', last_name='User')
        self.assertEqual(str(u), 'Test User')
        u2 = User(username='testuser2')
        self.assertEqual(str(u2), 'testuser2')


class ThemeSettingsTest(BaseTest):
    def test_theme_created_on_access(self):
        theme, created = ThemeSettings.objects.get_or_create(user=self.master)
        self.assertTrue(created)
        self.assertEqual(theme.theme_name, 'modern')

    def test_theme_preset_modern(self):
        theme = ThemeSettings(user=self.master)
        theme.apply_preset('modern')
        self.assertEqual(theme.primary_color, '#2563eb')
        self.assertEqual(theme.button_style, 'rounded')

    def test_theme_preset_vibrant(self):
        theme = ThemeSettings(user=self.master)
        theme.apply_preset('vibrant')
        self.assertEqual(theme.primary_color, '#7c3aed')
        self.assertEqual(theme.button_style, 'pill')

    def test_theme_preset_dark_neumorphic(self):
        theme = ThemeSettings(user=self.master)
        theme.apply_preset('dark-neumorphic')
        self.assertEqual(theme.primary_color, '#10b981')
        self.assertEqual(theme.button_style, 'pill')

    def test_theme_str(self):
        theme = ThemeSettings(user=self.master, theme_name='modern')
        self.assertIn('master', str(theme))


class UserActivityLogTest(BaseTest):
    def test_log_creation(self):
        log_user_action(self.master, 'login', details='Test login')
        self.assertEqual(UserActivityLog.objects.count(), 1)
        log_entry = UserActivityLog.objects.first()
        self.assertEqual(log_entry.username, 'master')
        self.assertEqual(log_entry.action, 'login')

    def test_log_model_save_signal(self):
        set_current_user(self.master)
        cliente = Cliente.objects.create(
            nombre='Test Client',
            telefono='+521234567890',
            dispositivo_id='AA:BB:CC:DD:EE:FF',
        )
        self.assertGreaterEqual(UserActivityLog.objects.filter(model_name='Cliente', action='create').count(), 1)

    def test_log_model_update_signal(self):
        set_current_user(self.master)
        cliente = Cliente.objects.create(
            nombre='Test Client',
            telefono='+521234567890',
            dispositivo_id='AA:BB:CC:DD:EE:01',
        )
        UserActivityLog.objects.all().delete()
        cliente.nombre = 'Updated Client'
        cliente.save()
        self.assertGreaterEqual(UserActivityLog.objects.filter(model_name='Cliente', action='update').count(), 1)

    def test_log_ordering(self):
        UserActivityLog.objects.all().delete()
        log_user_action(self.master, 'login', details='First')
        import time; time.sleep(0.01)
        log_user_action(self.master, 'logout', details='Second')
        logs = UserActivityLog.objects.all()
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0].action, 'logout')
        self.assertEqual(logs[1].action, 'login')

    def test_log_without_user(self):
        cnt_before = UserActivityLog.objects.count()
        log_user_action(None, 'login')
        self.assertEqual(UserActivityLog.objects.count(), cnt_before)

    def test_log_str(self):
        UserActivityLog.objects.all().delete()
        log_user_action(self.master, 'login', details='Test')
        log_entry = UserActivityLog.objects.first()
        self.assertIn('master', str(log_entry))
        self.assertIn('Inicio de sesión', str(log_entry))


class HomePageTest(BaseTest):
    def test_home_redirects_authenticated(self):
        r = self.client_master.get(reverse('home'))
        self.assertEqual(r.status_code, 302)


class ProfileViewTest(BaseTest):
    def test_profile_view_get(self):
        r = self.client_master.get(reverse('profile'))
        self.assertEqual(r.status_code, 200)

    def test_profile_view_post(self):
        r = self.client_master.post(reverse('profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@test.com',
        }, follow=True)
        self.master.refresh_from_db()
        self.assertEqual(self.master.first_name, 'Updated')
        self.assertEqual(r.status_code, 200)

    def test_profile_requires_login(self):
        r = self.client.get(reverse('profile'))
        self.assertEqual(r.status_code, 302)


class ThemeViewTest(BaseTest):
    def test_theme_view_get(self):
        r = self.client_master.get(reverse('theme'))
        self.assertEqual(r.status_code, 200)

    def test_theme_view_post(self):
        ThemeSettings.objects.create(user=self.master)
        r = self.client_master.post(reverse('theme'), {
            'theme_name': 'vibrant',
            'primary_color': '#7c3aed',
            'secondary_color': '#6d28d9',
            'bg_color': '#f5f3ff',
            'text_color': '#1e1b4b',
            'card_bg': '#ffffff',
            'sidebar_bg': '#2e1065',
            'button_style': 'pill',
            'custom_css': '',
            'pixel_bg': 'none',
            'text_border_color': '',
            'text_border_width': '0',
            'text_bold': 'on',
            'text_italic': '',
            'text_underline': '',
            'text_strikethrough': '',
            'apply_preset': '',
        })
        self.assertEqual(r.status_code, 302)
        theme = ThemeSettings.objects.get(user=self.master)
        self.assertEqual(theme.primary_color, '#7c3aed')

    def test_theme_requires_login(self):
        r = self.client.get(reverse('theme'))
        self.assertEqual(r.status_code, 302)

    def test_theme_all_presets(self):
        for preset_name, _ in ThemeSettings.THEME_CHOICES:
            theme = ThemeSettings(user=self.master)
            theme.apply_preset(preset_name)
            self.assertIsNotNone(theme.primary_color)


class ActivityLogsViewTest(BaseTest):
    def test_activity_logs_view_get(self):
        r = self.client_master.get(reverse('activity_logs'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Registro de Actividad')

    def test_activity_logs_accessible_by_support(self):
        r = self.client_soporte.get(reverse('activity_logs'))
        self.assertEqual(r.status_code, 200)

    def test_activity_logs_requires_login(self):
        r = self.client.get(reverse('activity_logs'))
        self.assertEqual(r.status_code, 302)

    def test_activity_log_delete_by_master(self):
        log = UserActivityLog.objects.create(
            user=self.master, username='master', action='login'
        )
        r = self.client_master.post(reverse('activity_log_delete', args=[log.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(UserActivityLog.objects.filter(pk=log.pk).exists())

    def test_activity_log_delete_by_non_master(self):
        log = UserActivityLog.objects.create(
            user=self.master, username='master', action='login'
        )
        r = self.client_admin.post(reverse('activity_log_delete', args=[log.pk]), follow=True)
        self.assertContains(r, 'Solo el administrador maestro')
        self.assertTrue(UserActivityLog.objects.filter(pk=log.pk).exists())


class PasswordChangeTest(BaseTest):
    def test_password_change(self):
        r = self.client_master.post(reverse('change_password'), {
            'old_password': 'master123',
            'new_password1': 'NewMaster123!',
            'new_password2': 'NewMaster123!',
        })
        self.assertEqual(r.status_code, 302)
        self.master.refresh_from_db()
        self.assertTrue(self.master.check_password('NewMaster123!'))

    def test_password_change_requires_login(self):
        r = self.client.get(reverse('change_password'))
        self.assertEqual(r.status_code, 302)


class PermissionTest(BaseTest):
    def test_support_can_create_client(self):
        r = self.client_soporte.post(reverse('cliente_create'), {
            'nombre': 'Support Client',
            'telefono': '+521111111111',
            'dispositivo_id': 'AA:BB:CC:DD:EE:11',
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Cliente.objects.filter(nombre='Support Client').exists())

    def test_support_can_view_client(self):
        Cliente.objects.create(nombre='Test', telefono='+521111111112', dispositivo_id='AA:BB:CC:DD:EE:22')
        r = self.client_soporte.get(reverse('cliente_list'))
        self.assertEqual(r.status_code, 200)

    def test_support_can_edit_client(self):
        c = Cliente.objects.create(nombre='Old', telefono='+521111111113', dispositivo_id='AA:BB:CC:DD:EE:33')
        r = self.client_soporte.post(reverse('cliente_update', args=[c.pk]), {
            'nombre': 'Updated',
            'telefono': '+521111111113',
            'dispositivo_id': 'AA:BB:CC:DD:EE:33',
        })
        self.assertEqual(r.status_code, 302)
        c.refresh_from_db()
        self.assertEqual(c.nombre, 'Updated')

    def test_support_cannot_delete_client(self):
        c = Cliente.objects.create(nombre='ToDelete', telefono='+521111111114', dispositivo_id='AA:BB:CC:DD:EE:44')
        r = self.client_soporte.post(reverse('cliente_delete', args=[c.pk]))
        self.assertEqual(r.status_code, 403)

    def test_support_can_create_subscription(self):
        c = Cliente.objects.create(nombre='Sub Client', telefono='+521111111115', dispositivo_id='AA:BB:CC:DD:EE:55')
        r = self.client_soporte.post(reverse('suscripcion_create'), {
            'cliente': c.pk,
            'plan': self.plan.pk,
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Suscripcion.objects.filter(cliente=c).exists())

    def test_support_cannot_access_finance_create(self):
        r = self.client_soporte.get(reverse('movimiento_create'))
        self.assertEqual(r.status_code, 403)

    def test_support_can_view_finance(self):
        r = self.client_soporte.get(reverse('movimiento_list'))
        self.assertEqual(r.status_code, 200)


class ContextProcessorTest(BaseTest):
    def test_theme_context_authenticated(self):
        r = self.client_master.get(reverse('dashboard'))
        self.assertIn('theme_primary', r.context)

    def test_theme_context_default_values(self):
        from apps.accounts.context_processors import theme_context
        class MockRequest:
            user = type('AnonymousUser', (), {'is_authenticated': False})()
        ctx = theme_context(MockRequest())
        self.assertEqual(ctx['theme_primary'], '#2563eb')


class TareaModelTest(BaseTest):
    def test_create_tarea(self):
        t = Tarea.objects.create(usuario=self.master, titulo='Test tarea', prioridad='alta')
        self.assertEqual(str(t), 'Test tarea')
        self.assertFalse(t.completada)

    def test_tarea_prioridad_default(self):
        t = Tarea.objects.create(usuario=self.master, titulo='Tarea default')
        self.assertEqual(t.prioridad, 'media')

    def test_tarea_ordering(self):
        Tarea.objects.create(usuario=self.master, titulo='Baja', prioridad='baja')
        Tarea.objects.create(usuario=self.master, titulo='Alta', prioridad='alta')
        tareas = Tarea.objects.filter(usuario=self.master)
        self.assertEqual(tareas.count(), 2)


class TareaViewTest(BaseTest):
    def test_todo_list_get(self):
        r = self.client_master.get(reverse('todo_list'))
        self.assertEqual(r.status_code, 200)

    def test_todo_create(self):
        r = self.client_master.post(reverse('todo_create'), {'titulo': 'Nueva tarea', 'prioridad': 'alta', 'categoria': 'general'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Tarea.objects.filter(titulo='Nueva tarea').exists())

    def test_todo_toggle(self):
        t = Tarea.objects.create(usuario=self.master, titulo='Toggle test')
        r = self.client_master.get(reverse('todo_toggle', args=[t.pk]))
        self.assertEqual(r.status_code, 302)
        t.refresh_from_db()
        self.assertTrue(t.completada)

    def test_todo_delete(self):
        t = Tarea.objects.create(usuario=self.master, titulo='Delete test')
        r = self.client_master.post(reverse('todo_delete', args=[t.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Tarea.objects.filter(pk=t.pk).exists())

    def test_todo_requires_login(self):
        r = self.client.get(reverse('todo_list'))
        self.assertEqual(r.status_code, 302)


class UserListViewTest(BaseTest):
    def test_user_list_master(self):
        r = self.client_master.get(reverse('user_list'))
        self.assertEqual(r.status_code, 200)

    def test_user_list_gerente(self):
        r = self.client_admin.get(reverse('user_list'))
        self.assertEqual(r.status_code, 200)

    def test_user_list_soporte_blocked(self):
        r = self.client_soporte.get(reverse('user_list'))
        self.assertEqual(r.status_code, 302)

    def test_user_list_anonymous_blocked(self):
        r = self.client.get(reverse('user_list'))
        self.assertEqual(r.status_code, 302)


class SuscripcionConDescuentoTest(BaseTest):
    def test_descuento_porcentaje(self):
        from apps.subscriptions.models import Suscripcion
        c = Cliente.objects.create(nombre='Test', telefono='+521111111116', dispositivo_id='AA:BB:CC:DD:EE:66')
        s = Suscripcion.objects.create(cliente=c, plan=self.plan, descuento_tipo='porcentaje', descuento_valor=10)
        self.plan.refresh_from_db()
        expected = self.plan.precio * Decimal('0.9')
        self.assertEqual(s.get_precio_final(), expected)

    def test_descuento_fijo(self):
        from apps.subscriptions.models import Suscripcion
        c = Cliente.objects.create(nombre='Test2', telefono='+521111111117', dispositivo_id='AA:BB:CC:DD:EE:77')
        s = Suscripcion.objects.create(cliente=c, plan=self.plan, descuento_tipo='fijo', descuento_valor=50)
        expected = max(0, self.plan.precio - 50)
        self.assertEqual(s.get_precio_final(), expected)


class MovimientoFinancieroEditTest(BaseTest):
    def test_movimiento_update_view(self):
        from apps.finance.models import MovimientoFinanciero
        m = MovimientoFinanciero.objects.create(tipo='ingreso', monto=100, descripcion='Test')
        r = self.client_master.get(reverse('movimiento_update', args=[m.pk]))
        self.assertEqual(r.status_code, 200)

    def test_movimiento_update_post(self):
        from apps.finance.models import MovimientoFinanciero
        m = MovimientoFinanciero.objects.create(tipo='ingreso', monto=100, descripcion='Original')
        r = self.client_master.post(reverse('movimiento_update', args=[m.pk]), {
            'tipo': 'egreso', 'monto': 200, 'descripcion': 'Actualizado'
        })
        self.assertEqual(r.status_code, 302)
        m.refresh_from_db()
        self.assertEqual(m.monto, 200)
        self.assertEqual(m.descripcion, 'Actualizado')


class LoginLogoutTest(BaseTest):
    def test_login_creates_log(self):
        u = User.objects.create_user(username='logintest', password='test12345')
        self.client.post(reverse('login'), {'username': 'logintest', 'password': 'test12345'})
        self.assertGreaterEqual(UserActivityLog.objects.filter(action='login', username='logintest').count(), 1)

    def test_logout_creates_log(self):
        self.client_master.get(reverse('logout'))
        self.assertGreaterEqual(UserActivityLog.objects.filter(action='logout', username='master').count(), 1)
