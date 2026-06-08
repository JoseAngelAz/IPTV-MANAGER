from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import Suscripcion, Plan
from .forms import SuscripcionForm
from apps.clients.models import Cliente
from django.db.models import F


def _aplicar_cortesia(suscripcion):
    if suscripcion.get_precio_final() == 0:
        suscripcion.metodo_pago = Suscripcion.MetodoPago.CORTESIA
        suscripcion.save(update_fields=['metodo_pago'])


class SuscripcionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Suscripcion
    template_name = 'subscriptions/suscripcion_list.html'
    context_object_name = 'suscripciones'
    paginate_by = 20
    permission_required = 'subscriptions.view_suscripcion'

    def get_queryset(self):
        qs = super().get_queryset().select_related('cliente', 'plan')
        estado = self.request.GET.get('estado')
        if estado:
            qs = qs.filter(estado=estado)
        return qs


class SuscripcionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Suscripcion
    form_class = SuscripcionForm
    template_name = 'subscriptions/suscripcion_form.html'
    permission_required = 'subscriptions.add_suscripcion'

    def get_success_url(self):
        return reverse_lazy('suscripcion_list')

    def form_valid(self, form):
        resp = super().form_valid(form)
        _aplicar_cortesia(form.instance)
        messages.success(self.request, 'Suscripción creada exitosamente.')
        return resp

    def get_initial(self):
        initial = super().get_initial()
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            initial['cliente'] = cliente_id
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['planes_precios'] = Plan.objects.filter(activo=True).values('id', 'precio')
        ctx['editando'] = False
        return ctx


class SuscripcionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Suscripcion
    form_class = SuscripcionForm
    template_name = 'subscriptions/suscripcion_form.html'
    permission_required = 'subscriptions.change_suscripcion'

    def get_success_url(self):
        return reverse_lazy('suscripcion_list')

    def form_valid(self, form):
        resp = super().form_valid(form)
        _aplicar_cortesia(form.instance)
        messages.success(self.request, 'Suscripción actualizada exitosamente.')
        return resp

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['planes_precios'] = Plan.objects.filter(activo=True).values('id', 'precio')
        ctx['editando'] = True
        return ctx


@login_required
@permission_required('subscriptions.change_suscripcion', raise_exception=True)
def suscripcion_cancel(request, pk):
    suscripcion = get_object_or_404(Suscripcion, pk=pk)
    if request.method == 'POST':
        suscripcion.estado = Suscripcion.Estado.CANCELADO
        suscripcion.save()
        messages.success(request, 'Suscripción cancelada.')
    return redirect('suscripcion_list')


@login_required
@permission_required('subscriptions.add_suscripcion', raise_exception=True)
def suscripcion_renew(request, pk):
    suscripcion_anterior = get_object_or_404(Suscripcion, pk=pk)
    if request.method == 'POST':
        Suscripcion.objects.create(
            cliente=suscripcion_anterior.cliente,
            plan=suscripcion_anterior.plan,
        )
        messages.success(request, 'Suscripción renovada.')
    return redirect('suscripcion_list')
