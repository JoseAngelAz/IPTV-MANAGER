from django.urls import path
from . import views

urlpatterns = [
    path('', views.MovimientoListView.as_view(), name='movimiento_list'),
    path('nuevo/', views.MovimientoCreateView.as_view(), name='movimiento_create'),
]
