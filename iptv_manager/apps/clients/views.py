from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.decorators import method_decorator
from .models import Cliente, HistorialCliente, Nota
from .forms import ClienteForm
from apps.subscriptions.models import Suscripcion


class ClienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Cliente
    template_name = 'clients/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 20
    permission_required = 'clients.view_cliente'

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(nombre__icontains=q) | qs.filter(telefono__icontains=q) | qs.filter(dispositivo_id__icontains=q)
        return qs


class ClienteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clients/cliente_form.html'
    permission_required = 'clients.add_cliente'

    def get_success_url(self):
        return reverse_lazy('cliente_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        resp = super().form_valid(form)
        HistorialCliente.objects.create(
            cliente=self.object,
            usuario=self.request.user,
            cambio=f'Cliente creado por {self.request.user.get_full_name() or self.request.user.username}'
        )
        messages.success(self.request, 'Cliente creado exitosamente.')
        return resp


class ClienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clients/cliente_form.html'
    permission_required = 'clients.change_cliente'

    def get_success_url(self):
        return reverse_lazy('cliente_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        resp = super().form_valid(form)
        HistorialCliente.objects.create(
            cliente=self.object,
            usuario=self.request.user,
            cambio=f'Datos actualizados por {self.request.user.get_full_name() or self.request.user.username}'
        )
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return resp


class ClienteDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Cliente
    template_name = 'clients/cliente_detail.html'
    context_object_name = 'cliente'
    permission_required = 'clients.view_cliente'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['suscripciones'] = self.object.suscripciones.all()
        ctx['historial'] = self.object.historial.all()[:20]
        ctx['notas'] = self.object.notas.all()[:20]
        return ctx


@login_required
@permission_required('clients.change_cliente', raise_exception=True)
def agregar_nota(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        nota = request.POST.get('nota', '').strip()
        if nota:
            HistorialCliente.objects.create(
                cliente=cliente,
                usuario=request.user,
                cambio=nota
            )
            messages.success(request, 'Nota agregada.')
    return redirect('cliente_detail', pk=pk)


@login_required
@permission_required('clients.delete_cliente', raise_exception=True)
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.activo = False
        cliente.save()
        messages.success(request, 'Cliente desactivado.')
        return redirect('cliente_list')
    return render(request, 'clients/cliente_confirm_delete.html', {'cliente': cliente})


@login_required
@permission_required('clients.change_cliente', raise_exception=True)
def nota_create(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        contenido = request.POST.get('contenido', '').strip()
        if contenido:
            Nota.objects.create(cliente=cliente, usuario=request.user, contenido=contenido)
            messages.success(request, 'Nota agregada.')
    return redirect('cliente_detail', pk=pk)


@login_required
@permission_required('clients.change_cliente', raise_exception=True)
def nota_update(request, pk):
    nota = get_object_or_404(Nota, pk=pk)
    if request.method == 'POST':
        contenido = request.POST.get('contenido', '').strip()
        if contenido:
            nota.contenido = contenido
            nota.save()
            messages.success(request, 'Nota actualizada.')
        return redirect('cliente_detail', pk=nota.cliente.pk)
    return render(request, 'clients/nota_form.html', {'nota': nota})


@login_required
@permission_required('clients.delete_cliente', raise_exception=True)
def nota_delete(request, pk):
    nota = get_object_or_404(Nota, pk=pk)
    cliente_pk = nota.cliente.pk
    if request.method == 'POST':
        nota.delete()
        messages.success(request, 'Nota eliminada.')
        return redirect('cliente_detail', pk=cliente_pk)
    return render(request, 'clients/nota_confirm_delete.html', {'nota': nota})
