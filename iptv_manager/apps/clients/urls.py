from django.urls import path
from apps.accounts.views import dashboard
from . import views

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/nuevo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/eliminar/', views.cliente_delete, name='cliente_delete'),
    path('clientes/<int:pk>/nota/', views.agregar_nota, name='agregar_nota'),
    path('clientes/<int:pk>/anotacion/', views.nota_create, name='nota_create'),
    path('anotaciones/<int:pk>/editar/', views.nota_update, name='nota_update'),
    path('anotaciones/<int:pk>/eliminar/', views.nota_delete, name='nota_delete'),
]