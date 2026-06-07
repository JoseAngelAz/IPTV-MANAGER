from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import MovimientoFinanciero
from .forms import MovimientoForm


class MovimientoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = MovimientoFinanciero
    template_name = 'finance/movimiento_list.html'
    context_object_name = 'movimientos'
    paginate_by = 20
    permission_required = 'finance.view_movimientofinanciero'

    def get_queryset(self):
        qs = super().get_queryset().select_related('suscripcion__cliente')
        tipo = self.request.GET.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        return qs


class MovimientoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = MovimientoFinanciero
    form_class = MovimientoForm
    template_name = 'finance/movimiento_form.html'
    permission_required = 'finance.add_movimientofinanciero'

    def get_success_url(self):
        return reverse_lazy('movimiento_list')

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, 'Movimiento registrado.')
        return resp
