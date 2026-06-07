from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.profile_view, name='profile'),
    path('perfil/cambiar-password/', views.change_password_view, name='change_password'),
    path('tema/', views.theme_view, name='theme'),
    path('actividad/', views.activity_logs_view, name='activity_logs'),
    path('actividad/eliminar/', views.activity_log_delete, name='activity_log_bulk_delete'),
    path('actividad/<int:pk>/eliminar/', views.activity_log_delete, name='activity_log_delete'),
    path('documentacion/', views.documentation_view, name='documentation'),
    path('error-page-settings/', views.error_page_settings_view, name='error_page_settings'),
    path('error-page-settings/preview/', views.error_page_preview, name='error_page_preview'),
    path('session-config/', views.session_config_view, name='session_config'),
    path('extend-session/', views.extend_session, name='extend_session'),
    path('set-language/', views.set_language_view, name='set_language'),
]
