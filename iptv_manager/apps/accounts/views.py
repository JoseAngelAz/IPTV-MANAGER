import json
from collections import OrderedDict
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseNotAllowed
from .forms import LoginForm, ProfileForm, ThemeForm, CustomPresetForm, SessionConfigForm
from .models import ThemeSettings, UserActivityLog, CustomPreset, ErrorPageSettings, SessionConfig, log_user_action
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
    }
    return render(request, 'dashboard.html', context)
