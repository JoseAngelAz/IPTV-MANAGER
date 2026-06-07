from django.urls import path
from . import views

urlpatterns = [
    path('', views.SuscripcionListView.as_view(), name='suscripcion_list'),
    path('nueva/', views.SuscripcionCreateView.as_view(), name='suscripcion_create'),
    path('<int:pk>/cancelar/', views.suscripcion_cancel, name='suscripcion_cancel'),
    path('<int:pk>/renovar/', views.suscripcion_renew, name='suscripcion_renew'),
]
