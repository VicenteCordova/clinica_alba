"""
apps/personas/views.py
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib import messages

from apps.core.mixins import RolRequeridoMixin
from apps.personas.models import Persona, Sexo
from apps.pacientes.forms import PersonaBaseForm
from apps.auditoria.models import Bitacora


class PersonaListView(RolRequeridoMixin, ListView):
    roles_permitidos = ["administrador", "administrativo", "recepcionista"]
    template_name = "personas/lista.html"
    context_object_name = "personas"
    paginate_by = 25
    queryset = Persona.objects.select_related("id_sexo").order_by(
        "apellido_paterno", "nombres"
    )

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(rut__icontains=q) | qs.filter(nombres__icontains=q) | qs.filter(apellido_paterno__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class PersonaCrearView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista"]
    template_name = "personas/crear.html"

    def get(self, request):
        return render(request, self.template_name, {"form": PersonaBaseForm()})

    def post(self, request):
        form = PersonaBaseForm(data=request.POST)
        if form.is_valid():
            persona = form.save()
            Bitacora.registrar(
                usuario=request.user,
                modulo="personas",
                accion="creacion",
                tabla_afectada="personas",
                id_registro_afectado=persona.id_persona,
                descripcion=f"Persona creada: {persona.nombre_completo}",
                ip_origen=getattr(request, "ip_origen", None),
            )
            messages.success(request, f"Persona {persona.nombre_completo} registrada.")
            return redirect("personas:detalle", pk=persona.id_persona)
        return render(request, self.template_name, {"form": form})


class PersonaDetalleView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista"]
    template_name = "personas/detalle.html"

    def get(self, request, pk):
        persona = get_object_or_404(Persona.objects.select_related("id_sexo"), pk=pk)
        return render(request, self.template_name, {"persona": persona})


class PersonaEditarView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador", "administrativo", "recepcionista"]
    template_name = "personas/editar.html"

    def get(self, request, pk):
        persona = get_object_or_404(Persona, pk=pk)
        return render(request, self.template_name, {
            "form": PersonaBaseForm(instance=persona),
            "persona": persona,
        })

    def post(self, request, pk):
        persona = get_object_or_404(Persona, pk=pk)
        form = PersonaBaseForm(data=request.POST, instance=persona)
        if form.is_valid():
            form.save()
            Bitacora.registrar(
                usuario=request.user,
                modulo="personas",
                accion="edicion",
                tabla_afectada="personas",
                id_registro_afectado=persona.id_persona,
                descripcion=f"Persona editada: {persona.nombre_completo}",
                ip_origen=getattr(request, "ip_origen", None),
            )
            messages.success(request, "Datos actualizados correctamente.")
            return redirect("personas:detalle", pk=pk)
        return render(request, self.template_name, {"form": form, "persona": persona})
