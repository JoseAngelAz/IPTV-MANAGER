import json
from collections import OrderedDict
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseNotAllowed
from .forms import LoginForm, ProfileForm, ThemeForm, CustomPresetForm, SessionConfigForm, LandingPageConfigForm, TareaForm, RecordatorioTemplateForm
from .models import ThemeSettings, UserActivityLog, CustomPreset, ErrorPageSettings, SessionConfig, LandingPageConfig, WhatsAppConfig, RecordatorioTemplate, log_user_action, Tarea, User
from apps.clients.models import Cliente
from apps.subscriptions.models import Suscripcion, Plan
from apps.finance.models import MovimientoFinanciero


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    stats = {
        'total_planes': Plan.objects.filter(activo=True).count(),
        'suscripciones_activas': Suscripcion.objects.filter(estado=Suscripcion.Estado.ACTIVO).count(),
        'total_clientes': Cliente.objects.filter(activo=True).count(),
    }
    return render(request, 'home.html', {'stats': stats})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_user_action(user, 'login', details='Inicio de sesión', request=request)
            return redirect('dashboard')
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_user_action(request.user, 'logout', details='Cierre de sesión', request=request)
    logout(request)
    return redirect('login')


@login_required
def about(request):
    return render(request, 'about.html')


@login_required
def documentation_view(request):
    section = request.GET.get('seccion', 'tecnologia')
    return render(request, 'documentation.html', {'section': section})


def custom_404(request, exception=None):
    settings = ErrorPageSettings.get_settings()
    return render(request, '404.html', {
        'error_settings': settings,
        'pixel_css': _get_pixel_art_css() if settings.show_pixel_art else '',
    }, status=404)


def _get_pixel_art_css():
    return '''
.pixel-bg { position: fixed; inset: 0; z-index: 0; overflow: hidden; }
.pixel-ground { position: absolute; bottom: 0; left: 0; right: 0; height: 40%;
  background: repeating-linear-gradient(0deg, #2d1b69 0px, #2d1b69 4px, #3d2b79 4px, #3d2b79 8px); }
.pixel-castle { position: absolute; bottom: 35%; left: 50%; transform: translateX(-50%);
  image-rendering: pixelated; font-size: 0; }
.pixel-castle div { display: inline-block; vertical-align: bottom; }
.pixel-tower { width: 20px; height: 80px; background: #4a3a8a; margin: 0 2px;
  box-shadow: -2px 0 #3d2b79, 2px 0 #5a4a9a; }
.pixel-wall { width: 40px; height: 60px; background: #4a3a8a; margin: 0 2px;
  box-shadow: -2px 0 #3d2b79, 2px 0 #5a4a9a; }
.pixel-roof { width: 0; height: 0; border-left: 15px solid transparent; border-right: 15px solid transparent;
  border-bottom: 20px solid #6b5bae; margin-bottom: -2px; }
.pixel-door { width: 12px; height: 25px; background: #2d1b69; margin: 35px auto 0; border-radius: 6px 6px 0 0; }
.pixel-window { width: 10px; height: 10px; background: #fbbf24; margin: 10px auto 0;
  box-shadow: 0 0 6px #fbbf24; }
.pixel-star { position: absolute; background: #fff; width: 3px; height: 3px;
  box-shadow: 0 0 4px rgba(255,255,255,0.8); animation: twinkle 2s ease-in-out infinite; }
@keyframes twinkle { 0%,100% { opacity: 0.3; } 50% { opacity: 1; } }
.pixel-message { position: relative; z-index: 1; text-align: center; padding-top: 10vh; }
'''


@login_required
def error_page_settings_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'Solo el administrador maestro puede personalizar la página 404.')
        return redirect('dashboard')
    settings = ErrorPageSettings.get_settings()
    if request.method == 'POST':
        settings.title = request.POST.get('title', settings.title)
        settings.message = request.POST.get('message', settings.message)
        settings.show_pixel_art = request.POST.get('show_pixel_art') == 'on'
        settings.bg_color = request.POST.get('bg_color', settings.bg_color)
        settings.text_color = request.POST.get('text_color', settings.text_color)
        settings.updated_by = request.user
        settings.save()
        log_user_action(request.user, 'update', 'ErrorPageSettings', 'Configuración 404',
                       details='Actualizó la configuración de la página 404', request=request)
        messages.success(request, 'Configuración de página 404 actualizada.')
        return redirect('error_page_settings')
    return render(request, 'accounts/error_page_settings.html', {'settings': settings})


@login_required
def error_page_preview(request):
    settings = ErrorPageSettings.get_settings()
    return render(request, '404.html', {
        'error_settings': settings,
        'pixel_css': _get_pixel_art_css() if settings.show_pixel_art else '',
    })


def custom_500(request, exception=None):
    settings = ErrorPageSettings.get_settings()
    err_url = request.build_absolute_uri()
    err_user = request.user if request.user.is_authenticated else None
    return render(request, '500.html', {
        'error_settings': settings,
        'pixel_css': _get_pixel_art_css_500() if settings.show_pixel_art_500 else '',
        'error_url': err_url,
        'error_user': err_user,
    }, status=500)


@login_required
def error_report_view(request):
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()
        url = request.POST.get('url', '')
        if descripcion:
            from .models import ErrorReport
            ErrorReport.objects.create(
                url=url or request.META.get('HTTP_REFERER', ''),
                descripcion=descripcion,
                user=request.user if request.user.is_authenticated else None,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )
            messages.success(request, 'Reporte de error enviado. Gracias por ayudarnos a mejorar.')
        else:
            messages.error(request, 'Describe el error para poder reportarlo.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def _get_pixel_art_css_500():
    return '''
.pixel-bg { position: fixed; inset: 0; z-index: 0; overflow: hidden; }
.pixel-volcano { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 120px; height: 180px; image-rendering: pixelated; }
.pixel-mountain-bg { position: absolute; bottom: 30%; left: 0; right: 0; height: 60%;
  background: repeating-linear-gradient(90deg, #1a1a2e 0px, #1a1a2e 6px, #16213e 6px, #16213e 12px); }
.pixel-volcano-body { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 0; height: 0;
  border-left: 60px solid transparent; border-right: 60px solid transparent;
  border-bottom: 140px solid #2d1b00; }
.pixel-volcano-top { position: absolute; bottom: 130px; left: 50%; transform: translateX(-50%);
  width: 40px; height: 15px; background: #5c2e00;
  box-shadow: 0 0 20px #ff440066, 0 5px 0 #8b3a00; }
.pixel-lava { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 30px; height: 5px; background: #ff4400;
  animation: lava-flow 3s ease-in-out infinite; }
.pixel-lava::before { content: ''; position: absolute; left: -20px; top: 5px;
  width: 20px; height: 4px; background: #ff6600; }
.pixel-lava::after { content: ''; position: absolute; left: 30px; top: 5px;
  width: 20px; height: 4px; background: #ff6600; }
.pixel-fire { position: absolute; width: 6px; height: 6px;
  background: #ff4400; border-radius: 0;
  box-shadow: 0 0 8px #ff440088; }
.pixel-fire:nth-child(1) { bottom: 140px; left: 52%; animation: fire-rise 2s ease-in-out infinite; }
.pixel-fire:nth-child(2) { bottom: 145px; left: 46%; animation: fire-rise 2.5s ease-in-out infinite 0.5s; }
.pixel-fire:nth-child(3) { bottom: 150px; left: 50%; animation: fire-rise 1.8s ease-in-out infinite 0.3s; }
.pixel-fire:nth-child(4) { bottom: 135px; left: 48%; animation: fire-rise 3s ease-in-out infinite 0.8s; }
.pixel-fire:nth-child(5) { bottom: 147px; left: 54%; animation: fire-rise 2.2s ease-in-out infinite 1s; }
@keyframes fire-rise { 0% { transform: translateY(0) scale(1); opacity: 1; }
  100% { transform: translateY(-40px) scale(0.3); opacity: 0; } }
@keyframes lava-flow { 0%,100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(3px); } }
.pixel-ember { position: absolute; width: 3px; height: 3px; background: #ffaa00;
  border-radius: 0; box-shadow: 0 0 4px #ffaa00aa; }
.pixel-ember:nth-child(1) { top: 20%; left: 30%; animation: ember-float 4s ease-in-out infinite; }
.pixel-ember:nth-child(2) { top: 40%; left: 70%; animation: ember-float 5s ease-in-out infinite 1s; }
.pixel-ember:nth-child(3) { top: 10%; left: 50%; animation: ember-float 3.5s ease-in-out infinite 2s; }
.pixel-ember:nth-child(4) { top: 25%; left: 85%; animation: ember-float 4.5s ease-in-out infinite 0.5s; }
.pixel-ember:nth-child(5) { top: 35%; left: 15%; animation: ember-float 3s ease-in-out infinite 1.5s; }
.pixel-ember:nth-child(6) { top: 5%; left: 65%; animation: ember-float 5.5s ease-in-out infinite 3s; }
@keyframes ember-float { 0%,100% { transform: translate(0, 0); opacity: 0.3; }
  25% { transform: translate(-10px, -10px); opacity: 0.8; }
  50% { transform: translate(5px, -20px); opacity: 0.5; }
  75% { transform: translate(-5px, -15px); opacity: 0.8; } }
.pixel-broken-gear { position: absolute; width: 16px; height: 16px;
  background: transparent;
  box-shadow:
    0 0 0 4px #444, 0 12px 0 4px #444, 12px 0 0 4px #444, 12px 12px 0 4px #444,
    4px 4px 0 0 #ff4400, 8px 8px 0 0 #ff440066, 4px 8px 0 2px #ff660044;
  animation: gear-shake 3s ease-in-out infinite; }
.pixel-broken-gear:nth-child(7) { top: 50%; left: 10%; }
.pixel-broken-gear:nth-child(8) { top: 60%; right: 12%; animation-delay: 1s; }
@keyframes gear-shake { 0%,100% { transform: rotate(0deg); }
  25% { transform: rotate(15deg); } 75% { transform: rotate(-15deg); } }
'''


@login_required
def error_page_500_settings_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'Solo el administrador maestro puede personalizar la página 500.')
        return redirect('dashboard')
    settings = ErrorPageSettings.get_settings()
    if request.method == 'POST':
        settings.title_500 = request.POST.get('title_500', settings.title_500)
        settings.message_500 = request.POST.get('message_500', settings.message_500)
        settings.show_pixel_art_500 = request.POST.get('show_pixel_art_500') == 'on'
        settings.bg_color_500 = request.POST.get('bg_color_500', settings.bg_color_500)
        settings.text_color_500 = request.POST.get('text_color_500', settings.text_color_500)
        settings.updated_by = request.user
        settings.save()
        log_user_action(request.user, 'update', 'ErrorPageSettings', 'Configuración 500',
                       details='Actualizó la configuración de la página 500', request=request)
        messages.success(request, 'Configuración de página 500 actualizada.')
        return redirect('error_page_500_settings')
    return render(request, 'accounts/error_page_500_settings.html', {'settings': settings})


@login_required
def error_page_500_preview(request):
    settings = ErrorPageSettings.get_settings()
    return render(request, '500.html', {
        'error_settings': settings,
        'pixel_css': _get_pixel_art_css_500() if settings.show_pixel_art_500 else '',
    })


@login_required
def photo_gallery_view(request):
    from apps.clients.models import Cliente
    users = User.objects.exclude(profile_picture='').exclude(profile_picture__isnull=True)
    clients = Cliente.objects.exclude(foto='').exclude(foto__isnull=True)
    return render(request, 'accounts/photo_gallery.html', {'users': users, 'clients': clients})


@login_required
def session_config_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'Solo el administrador maestro puede configurar la sesión.')
        return redirect('dashboard')
    config = SessionConfig.get_config()
    if request.method == 'POST':
        form = SessionConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            request.session.set_expiry(config.timeout_minutes * 60)
            log_user_action(request.user, 'update', 'SessionConfig', 'Configuración de sesión',
                           details=f'Cambió tiempo de sesión a {config.timeout_minutes} minutos',
                           request=request)
            messages.success(request, f'Tiempo de sesión actualizado a {config.timeout_minutes} minutos.')
            return redirect('session_config')
    else:
        form = SessionConfigForm(instance=config)
    return render(request, 'accounts/session_config.html', {'form': form, 'config': config})


@login_required
def landing_page_config_view(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Gerente', 'Superadmin']).exists()):
        messages.error(request, 'Solo administradores y gerentes pueden configurar la página de inicio.')
        return redirect('dashboard')
    config = LandingPageConfig.get_config()
    if request.method == 'POST':
        form = LandingPageConfigForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.updated_by = request.user
            instance.save()
            log_user_action(request.user, 'update', 'LandingPageConfig', 'Configuración de landing page',
                           details='Actualizó la configuración de la página de inicio',
                           request=request)
            messages.success(request, 'Configuración de página de inicio actualizada.')
            return redirect('landing_page_config')
        messages.error(request, 'Corrige los errores en el formulario.')
    else:
        form = LandingPageConfigForm(instance=config)
    return render(request, 'accounts/landing_page_config.html', {'form': form, 'config': config})


@login_required
def extend_session(request):
    if request.method == 'POST':
        config = SessionConfig.get_config()
        request.session.set_expiry(config.timeout_minutes * 60)
        return JsonResponse({'status': 'ok', 'minutes': config.timeout_minutes})
    return HttpResponseNotAllowed(['POST'])


def set_language_view(request):
    lang = request.GET.get('lang', 'es')
    if lang not in ['es', 'en']:
        lang = 'es'
    request.session['django_language'] = lang
    next_url = request.GET.get('next', '/dashboard/')
    return redirect(next_url)


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            log_user_action(request.user, 'update', 'Perfil',
                          f'{request.user.get_full_name() or request.user.username}',
                          details='Actualización de perfil', request=request)
            messages.success(request, 'Perfil actualizado.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def theme_view(request):
    theme, _ = ThemeSettings.objects.get_or_create(user=request.user)
    custom_presets = CustomPreset.objects.filter(user=request.user)
    preset_form = CustomPresetForm()

    if request.method == 'POST':
        form = ThemeForm(request.POST, instance=theme)
        action = request.POST.get('action', 'save_theme')

        if action == 'save_preset':
            preset_form = CustomPresetForm(request.POST)
            if preset_form.is_valid():
                preset = preset_form.save(commit=False)
                preset.user = request.user
                if CustomPreset.objects.filter(user=request.user, name=preset.name).exists():
                    messages.error(request, f'Ya existe un preset con el nombre "{preset.name}".')
                else:
                    preset.save()
                    log_user_action(request.user, 'create', 'Preset Personalizado',
                                  str(preset), details=f'Creó preset personalizado "{preset.name}"',
                                  request=request)
                    messages.success(request, f'Preset "{preset.name}" guardado.')
                    return redirect('theme')
        elif action == 'delete_preset':
            preset_id = request.POST.get('preset_id')
            preset = get_object_or_404(CustomPreset, pk=preset_id, user=request.user)
            preset.delete()
            messages.success(request, 'Preset eliminado.')
            return redirect('theme')
        elif action == 'apply_custom_preset':
            preset_id = request.POST.get('preset_id')
            preset = get_object_or_404(CustomPreset, pk=preset_id, user=request.user)
            preset.apply_to(theme)
            theme.save()
            messages.success(request, f'Preset "{preset.name}" aplicado.')
            return redirect('theme')
        else:
            if form.is_valid():
                theme = form.save(commit=False)
                if form.cleaned_data.get('apply_preset') and form.cleaned_data['apply_preset'] != theme.theme_name:
                    theme.apply_preset(form.cleaned_data['apply_preset'])
                theme.save()
                log_user_action(request.user, 'update', 'Tema',
                              f'Tema: {theme.get_theme_name_display()}',
                              details=f'Cambió tema a {theme.get_theme_name_display()}', request=request)
                messages.success(request, 'Tema actualizado.')
                return redirect('theme')
    else:
        form = ThemeForm(instance=theme)

    return render(request, 'accounts/theme.html', {
        'form': form, 'theme': theme, 'presets': ThemeSettings.THEME_CHOICES,
        'custom_presets': custom_presets, 'preset_form': preset_form,
    })


@login_required
def activity_logs_view(request):
    logs = UserActivityLog.objects.select_related('user').all()
    can_delete = request.user.is_superuser
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)
    return render(request, 'accounts/activity_logs.html', {
        'logs': logs_page,
        'can_delete': can_delete,
    })


@login_required
def activity_log_delete(request, pk=None):
    if not request.user.is_superuser:
        messages.error(request, 'Solo el administrador maestro puede eliminar registros.')
        return redirect('activity_logs')

    if request.method == 'POST' and not pk:
        pks = request.POST.getlist('selected_ids')
        if not pks:
            messages.warning(request, 'No seleccionaste ningún registro.')
            return redirect('activity_logs')
        count = UserActivityLog.objects.filter(pk__in=pks).count()
        UserActivityLog.objects.filter(pk__in=pks).delete()
        log_user_action(request.user, 'delete', 'Registro de Actividad',
                      f'{count} registros', details=f'Eliminó {count} registros de actividad en lote',
                      request=request)
        messages.success(request, f'{count} registros eliminados.')
        return redirect('activity_logs')

    log = get_object_or_404(UserActivityLog, pk=pk)
    log_user_action(request.user, 'delete', 'Registro de Actividad',
                  str(log), details=f'Eliminó registro de actividad #{pk}', request=request)
    log.delete()
    messages.success(request, 'Registro eliminado.')
    return redirect('activity_logs')


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_user_action(request.user, 'update', 'Contraseña',
                          f'{request.user.get_full_name() or request.user.username}',
                          details='Cambio de contraseña', request=request)
            messages.success(request, 'Contraseña actualizada.')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def user_list_view(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Superadmin', 'Gerente']).exists()):
        messages.error(request, 'No tienes permiso para ver esta sección.')
        return redirect('dashboard')
    usuarios = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'usuarios': usuarios})


@login_required
def todo_list(request):
    filtro = request.GET.get('filtro', 'todas')
    qs = Tarea.objects.filter(usuario=request.user)
    if filtro == 'pendientes':
        qs = qs.filter(completada=False)
    elif filtro == 'completadas':
        qs = qs.filter(completada=True)
    else:
        qs = qs
    return render(request, 'accounts/todo_list.html', {
        'tareas': qs,
        'filtro': filtro,
        'form': TareaForm(),
        'now': timezone.now(),
    })


@login_required
def todo_create(request):
    if request.method == 'POST':
        form = TareaForm(request.POST)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.usuario = request.user
            tarea.save()
            messages.success(request, 'Tarea creada.')
    return redirect('todo_list')


@login_required
def todo_toggle(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk, usuario=request.user)
    tarea.completada = not tarea.completada
    tarea.save()
    return redirect('todo_list')


@login_required
def todo_delete(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk, usuario=request.user)
    if request.method == 'POST':
        tarea.delete()
        messages.success(request, 'Tarea eliminada.')
    return redirect('todo_list')


def _whatsapp_base():
    from django.conf import settings
    url = settings.WHATSAPP_API_URL
    if url.endswith('/api/send'):
        return url[:-len('/api/send')]
    return url[:url.rfind('/')] if '/' in url else url


def _get_whatsapp_status():
    import requests
    base = _whatsapp_base()
    try:
        resp = requests.get(f'{base}/api/status', timeout=5)
        if resp.ok:
            return resp.json().get('status', 'disconnected')
    except Exception:
        pass
    return 'disconnected'


def _get_whatsapp_qr():
    import requests
    base = _whatsapp_base()
    try:
        resp = requests.get(f'{base}/api/qr', timeout=5)
        if resp.ok:
            return resp.json()
    except Exception:
        pass
    return {'qr': None, 'status': 'disconnected'}


@login_required
def whatsapp_config_view(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Superadmin', 'Gerente']).exists()):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')

    config = WhatsAppConfig.get_config()
    # Sync status and QR from the API
    status_data = _get_whatsapp_qr()
    config.session_status = status_data.get('status', 'disconnected')
    if status_data.get('qr'):
        config.qr_code = status_data['qr']
        config.last_qr_at = timezone.now()
    config.save(update_fields=['session_status', 'qr_code', 'last_qr_at', 'updated_at'])

    templates = RecordatorioTemplate.objects.all()
    return render(request, 'accounts/whatsapp_config.html', {
        'config': config,
        'templates': templates,
    })


@login_required
def whatsapp_qr_view(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Superadmin', 'Gerente']).exists()):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    data = _get_whatsapp_qr()
    config = WhatsAppConfig.get_config()
    if data.get('status') != config.session_status:
        config.session_status = data.get('status', 'disconnected')
        if data.get('qr'):
            config.qr_code = data['qr']
            config.last_qr_at = timezone.now()
        config.save()
    return JsonResponse(data)


@login_required
def whatsapp_status_view(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Superadmin', 'Gerente']).exists()):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    status = _get_whatsapp_status()
    WhatsAppConfig.objects.filter(pk=1).update(session_status=status)
    return JsonResponse({'status': status})


@login_required
def whatsapp_logout_view(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Superadmin', 'Gerente']).exists()):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('dashboard')

    import requests
    try:
        resp = requests.post(f'{_whatsapp_base()}/api/logout', timeout=10)
        if resp.ok:
            WhatsAppConfig.objects.filter(pk=1).update(
                session_status='disconnected',
                qr_code=None,
                last_qr_at=None,
            )
            messages.success(request, 'Sesión de WhatsApp cerrada correctamente.')
        else:
            messages.error(request, 'Error al cerrar sesión de WhatsApp.')
    except Exception as e:
        messages.error(request, f'Error de conexión: {e}')

    return redirect('whatsapp_config')


@login_required
def recordatorio_template_list(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Superadmin', 'Gerente']).exists()):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    templates = RecordatorioTemplate.objects.all()
    return render(request, 'accounts/recordatorio_template_list.html', {'templates': templates})


@login_required
def recordatorio_template_create(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Superadmin', 'Gerente']).exists()):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = RecordatorioTemplateForm(request.POST)
        if form.is_valid():
            tpl = form.save(commit=False)
            tpl.created_by = request.user
            tpl.save()
            log_user_action(request.user, 'create', 'RecordatorioTemplate', str(tpl),
                          details=f'Creó plantilla de recordatorio "{tpl.nombre}"', request=request)
            messages.success(request, f'Plantilla "{tpl.nombre}" creada.')
            return redirect('recordatorio_template_list')
    else:
        form = RecordatorioTemplateForm()
    return render(request, 'accounts/recordatorio_template_form.html', {'form': form, 'accion': 'Crear'})


@login_required
def recordatorio_template_edit(request, pk):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Superadmin', 'Gerente']).exists()):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('dashboard')
    tpl = get_object_or_404(RecordatorioTemplate, pk=pk)
    if request.method == 'POST':
        form = RecordatorioTemplateForm(request.POST, instance=tpl)
        if form.is_valid():
            form.save()
            log_user_action(request.user, 'update', 'RecordatorioTemplate', str(tpl),
                          details=f'Editó plantilla de recordatorio "{tpl.nombre}"', request=request)
            messages.success(request, f'Plantilla "{tpl.nombre}" actualizada.')
            return redirect('recordatorio_template_list')
    else:
        form = RecordatorioTemplateForm(instance=tpl)
    return render(request, 'accounts/recordatorio_template_form.html', {'form': form, 'accion': 'Editar'})


@login_required
def recordatorio_template_delete(request, pk):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Superadmin', 'Gerente']).exists()):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('dashboard')
    tpl = get_object_or_404(RecordatorioTemplate, pk=pk)
    if request.method == 'POST':
        nombre = tpl.nombre
        tpl.delete()
        log_user_action(request.user, 'delete', 'RecordatorioTemplate', nombre,
                      details=f'Eliminó plantilla de recordatorio "{nombre}"', request=request)
        messages.success(request, f'Plantilla "{nombre}" eliminada.')
        return redirect('recordatorio_template_list')
    return render(request, 'accounts/recordatorio_template_confirm_delete.html', {'tpl': tpl})


@login_required
def enviar_recordatorio_view(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Superadmin', 'Gerente']).exists()):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('dashboard')

    from apps.clients.models import Cliente

    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    templates = RecordatorioTemplate.objects.filter(activo=True)

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        template_ids = request.POST.getlist('templates')
        enviar_whatsapp = request.POST.get('enviar_whatsapp') == 'on'

        if not cliente_id:
            messages.error(request, 'Debes seleccionar un cliente.')
            return redirect('enviar_recordatorio')

        if not template_ids:
            messages.error(request, 'Debes seleccionar al menos una plantilla.')
            return redirect('enviar_recordatorio')

        cliente = get_object_or_404(Cliente, pk=cliente_id)
        selected_templates = RecordatorioTemplate.objects.filter(pk__in=template_ids, activo=True)

        if not selected_templates:
            messages.error(request, 'Las plantillas seleccionadas no están activas.')
            return redirect('enviar_recordatorio')

        if not cliente.telefono:
            messages.error(request, f'{cliente.nombre} no tiene teléfono registrado.')
            return redirect('enviar_recordatorio')

        if enviar_whatsapp:
            import requests
            from django.conf import settings

            enviados = 0
            fallidos = 0
            media_url = request.POST.get('media_url', '').strip()

            for tpl in selected_templates:
                suscripcion_activa = cliente.suscripciones.filter(estado='activo').first()
                mensaje = tpl.render(
                    cliente=cliente.nombre,
                    plan=suscripcion_activa.plan.nombre if suscripcion_activa else '',
                    vencimiento=suscripcion_activa.fecha_vencimiento.strftime('%d/%m/%Y') if suscripcion_activa else '',
                    precio=f'${suscripcion_activa.plan.precio:,.2f}' if suscripcion_activa else '',
                )

                payload = {'number': cliente.telefono, 'message': mensaje}
                if media_url:
                    payload['media'] = {'url': media_url}

                import requests as _wa_req
                try:
                    resp = _wa_req.post(
                        settings.WHATSAPP_API_URL,
                        json=payload,
                        timeout=15,
                    )
                    ok = resp.ok
                except Exception as e:
                    ok = False
                    resp_text = str(e)
                else:
                    resp_text = resp.text[:500]

                try:
                    LogNotificacion = __import__('apps.notifications.models', fromlist=['LogNotificacion']).LogNotificacion
                    LogNotificacion.objects.create(
                        cliente=cliente,
                        suscripcion=suscripcion_activa,
                        canal=LogNotificacion.Canal.WHATSAPP,
                        destinatario=cliente.telefono,
                        mensaje=mensaje,
                        enviado_ok=ok,
                        respuesta_api=resp_text,
                    )
                except Exception as log_err:
                    import logging
                    logging.getLogger(__name__).error(f'Error logging notification: {log_err}')

                if ok:
                    enviados += 1
                else:
                    fallidos += 1

            log_user_action(request.user, 'create', 'Recordatorio',
                          f'{cliente.nombre} — {enviados} enviados, {fallidos} fallidos',
                          details=f'Envío masivo de recordatorios a {cliente.nombre}',
                          request=request)

            if enviados:
                messages.success(request, f'{enviados} mensaje(s) enviado(s) a {cliente.nombre}.')
            if fallidos:
                messages.error(request, f'{fallidos} mensaje(s) fallaron al enviar a {cliente.nombre}.')
        else:
            messages.info(request, 'Modo vista previa — no se enviaron mensajes.')

        return redirect('enviar_recordatorio')

    # GET — renderizar página con preview en vivo
    clientes_json = []
    for c in clientes:
        sub = c.suscripciones.filter(estado='activo').first()
        clientes_json.append({
            'id': c.id,
            'nombre': c.nombre,
            'telefono': c.telefono,
            'plan': sub.plan.nombre if sub else '',
            'vencimiento': sub.fecha_vencimiento.strftime('%d/%m/%Y') if sub else '',
            'precio': f'${sub.plan.precio:,.2f}' if sub else '',
        })

    templates_json = []
    for t in templates:
        templates_json.append({
            'id': t.id,
            'nombre': t.nombre,
            'categoria': t.get_categoria_display(),
            'mensaje': t.mensaje,
        })

    import json as json_lib
    return render(request, 'accounts/enviar_recordatorio.html', {
        'clientes': clientes,
        'templates': templates,
        'clientes_json': json_lib.dumps(clientes_json),
        'templates_json': json_lib.dumps(templates_json),
    })


def _prediccion_lineal(valores):
    n = len(valores)
    if n < 2:
        return []
    xs = list(range(n))
    media_x = sum(xs) / n
    media_y = sum(valores) / n
    num = sum((x - media_x) * (y - media_y) for x, y in zip(xs, valores))
    den = sum((x - media_x) ** 2 for x in xs)
    pendiente = num / den if den else 0
    inter = media_y - pendiente * media_x
    return [pendiente * x + inter for x in range(n, n + 3)]


@login_required
def dashboard(request):
    hoy = timezone.now()
    en_3_dias = hoy + timezone.timedelta(days=3)

    meses = []
    labels_meses = []
    ingresos_mensuales = []
    egresos_mensuales = []
    for i in range(5, -1, -1):
        m = hoy.month - i
        y = hoy.year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        meses.append((m, y))
        labels_meses.append(f'{m:02d}/{y}')

    for m, y in meses:
        ing = MovimientoFinanciero.objects.filter(
            tipo=MovimientoFinanciero.Tipo.INGRESO,
            fecha__month=m, fecha__year=y
        ).aggregate(t=Sum('monto'))['t'] or 0
        eg = MovimientoFinanciero.objects.filter(
            tipo=MovimientoFinanciero.Tipo.EGRESO,
            fecha__month=m, fecha__year=y
        ).aggregate(t=Sum('monto'))['t'] or 0
        ingresos_mensuales.append(float(ing))
        egresos_mensuales.append(float(eg))

    netos_mensuales = [i - e for i, e in zip(ingresos_mensuales, egresos_mensuales)]
    predicciones = _prediccion_lineal(netos_mensuales)
    labels_prediccion = [f'Pred {i+1}' for i in range(len(predicciones))]

    planes = Plan.objects.filter(activo=True)
    plan_labels = [p.nombre for p in planes]
    plan_datos = [Suscripcion.objects.filter(plan=p, estado=Suscripcion.Estado.ACTIVO).count() for p in planes]

    suscripciones_activas = Suscripcion.objects.filter(estado=Suscripcion.Estado.ACTIVO)
    susc_por_dia = OrderedDict()
    for s in suscripciones_activas.order_by('fecha_inicio'):
        dia = s.fecha_inicio.strftime('%d/%m')
        susc_por_dia[dia] = susc_por_dia.get(dia, 0) + 1
    temporal_labels = list(susc_por_dia.keys())[-30:]
    temporal_datos = [susc_por_dia[d] for d in temporal_labels]

    # ── Messaging metrics ──────────────────────────────────────────
    from apps.notifications.models import LogNotificacion
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    msg_mes = LogNotificacion.objects.filter(fecha_envio__gte=inicio_mes)
    msg_total_mes = msg_mes.count()
    msg_ok_mes = msg_mes.filter(enviado_ok=True).count()
    msg_tasa_exito = round(msg_ok_mes / msg_total_mes * 100, 1) if msg_total_mes else 0
    msg_whatsapp_mes = msg_mes.filter(canal='whatsapp').count()
    msg_email_mes = msg_mes.filter(canal='email').count()

    # Daily messages last 30 days
    desde_30 = hoy - timezone.timedelta(days=30)
    msg_por_dia = OrderedDict()
    for i in range(30, -1, -1):
        dia = (hoy - timezone.timedelta(days=i)).strftime('%d/%m')
        msg_por_dia[dia] = 0
    for l in LogNotificacion.objects.filter(fecha_envio__gte=desde_30).values('fecha_envio', 'enviado_ok'):
        dia = l['fecha_envio'].strftime('%d/%m') if hasattr(l['fecha_envio'], 'strftime') else l['fecha_envio']
        if dia in msg_por_dia:
            msg_por_dia[dia] += 1
    msg_temporal_labels = list(msg_por_dia.keys())
    msg_temporal_datos = list(msg_por_dia.values())

    # Success/failure counts for pie chart
    msg_fallidos_mes = msg_total_mes - msg_ok_mes

    user_groups = list(request.user.groups.values_list('name', flat=True))
    context = {
        'user_display_name': request.user.get_full_name() or request.user.username,
        'user_groups': user_groups,
        'user_joined': request.user.date_joined,
        'user_last_login': request.user.last_login,
        'total_clientes': Cliente.objects.filter(activo=True).count(),
        'suscripciones_activas': suscripciones_activas.count(),
        'por_vencer': Suscripcion.objects.filter(
            estado=Suscripcion.Estado.ACTIVO,
            fecha_vencimiento__lte=en_3_dias,
            fecha_vencimiento__gte=hoy,
        ).count(),
        'vencidas': Suscripcion.objects.filter(estado=Suscripcion.Estado.VENCIDO).count(),
        'ingresos_mes': ingresos_mensuales[-1],
        'egresos_mes': egresos_mensuales[-1],
        'ultimos_movimientos': MovimientoFinanciero.objects.all()[:5],
        'ultimos_clientes': Cliente.objects.all()[:5],

        'chart_labels_meses': json.dumps(labels_meses),
        'chart_ingresos': json.dumps(ingresos_mensuales),
        'chart_egresos': json.dumps(egresos_mensuales),
        'chart_netos': json.dumps(netos_mensuales),

        'chart_plan_labels': json.dumps(plan_labels),
        'chart_plan_datos': json.dumps(plan_datos),

        'chart_temp_labels': json.dumps(temporal_labels),
        'chart_temp_datos': json.dumps(temporal_datos),

        'chart_pred_labels': json.dumps(labels_prediccion),
        'chart_pred_datos': json.dumps([round(p, 2) for p in predicciones]),

        # ── Messaging metrics ──
        'msg_total_mes': msg_total_mes,
        'msg_ok_mes': msg_ok_mes,
        'msg_tasa_exito': msg_tasa_exito,
        'msg_whatsapp_mes': msg_whatsapp_mes,
        'msg_email_mes': msg_email_mes,
        'msg_fallidos_mes': msg_fallidos_mes,
        'chart_msg_labels': json.dumps(msg_temporal_labels),
        'chart_msg_datos': json.dumps(msg_temporal_datos),
    }
    return render(request, 'dashboard.html', context)
