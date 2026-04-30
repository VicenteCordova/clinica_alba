"""
apps/accounts/views.py
"""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.accounts.forms import (
    AdminResetPasswordForm,
    CambiarPasswordForm,
    LoginForm,
    RolForm,
    UsuarioForm,
)
from apps.accounts.models import Rol, Usuario
from apps.auditoria.models import Bitacora
from apps.core.mixins import LoginRequeridoMixin, RolRequeridoMixin
from apps.pacientes.forms import PersonaBaseForm


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard:index")
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            usuario = form.get_usuario()
            login(request, usuario, backend="apps.accounts.backends.CustomAuthBackend")
            usuario.ultimo_acceso = timezone.now()
            usuario.save(update_fields=["ultimo_acceso"])
            Bitacora.registrar(
                usuario=usuario,
                modulo="accounts",
                accion="login",
                tabla_afectada="usuarios",
                id_registro_afectado=usuario.id_usuario,
                descripcion=f"Inicio de sesion: {usuario.username}",
                request=request,
            )
            messages.success(request, f"Bienvenido, {usuario.nombre_completo}.")
            return redirect(request.GET.get("next") or "dashboard:index")
        return render(request, self.template_name, {"form": form})


class LogoutView(LoginRequeridoMixin, View):
    def post(self, request):
        usuario = request.user
        Bitacora.registrar(
            usuario=usuario,
            modulo="accounts",
            accion="logout",
            tabla_afectada="usuarios",
            id_registro_afectado=usuario.id_usuario,
            descripcion=f"Cierre de sesion: {usuario.username}",
            request=request,
        )
        logout(request)
        messages.info(request, "Has cerrado sesion correctamente.")
        return redirect("accounts:login")


class CambiarPasswordView(LoginRequeridoMixin, View):
    template_name = "accounts/cambiar_password.html"

    def get(self, request):
        form = CambiarPasswordForm(usuario=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = CambiarPasswordForm(usuario=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            Bitacora.registrar(
                usuario=request.user,
                modulo="accounts",
                accion="cambio_password",
                tabla_afectada="usuarios",
                id_registro_afectado=request.user.id_usuario,
                descripcion="Contrasena cambiada por el usuario",
                request=request,
            )
            messages.success(request, "Tu contrasena fue actualizada correctamente.")
            return redirect("dashboard:index")
        return render(request, self.template_name, {"form": form})


class UsuarioListView(RolRequeridoMixin, ListView):
    roles_permitidos = ["administrador"]
    template_name = "accounts/usuarios_lista.html"
    context_object_name = "usuarios"
    paginate_by = 25

    def get_queryset(self):
        qs = Usuario.objects.select_related("id_persona").prefetch_related("usuario_roles__rol")
        estado = self.request.GET.get("estado", "")
        q = self.request.GET.get("q", "").strip()
        if estado:
            qs = qs.filter(estado_acceso=estado)
        if q:
            qs = qs.filter(username__icontains=q) | qs.filter(
                id_persona__nombres__icontains=q
            ) | qs.filter(id_persona__apellido_paterno__icontains=q)
        return qs.order_by("username")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["estado"] = self.request.GET.get("estado", "")
        return ctx


class UsuarioCrearView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]
    template_name = "accounts/usuario_form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "persona_form": PersonaBaseForm(prefix="persona"),
            "usuario_form": UsuarioForm(prefix="usuario"),
            "titulo": "Nuevo usuario",
        })

    def post(self, request):
        persona_form = PersonaBaseForm(data=request.POST, prefix="persona")
        usuario_form = UsuarioForm(data=request.POST, prefix="usuario")
        if persona_form.is_valid() and usuario_form.is_valid():
            with transaction.atomic():
                persona = persona_form.save()
                usuario = usuario_form.save(commit=False)
                usuario.id_persona = persona
                usuario.save()
                usuario_form.sync_roles(usuario)

            Bitacora.registrar(
                usuario=request.user,
                modulo="accounts",
                accion="creacion_usuario",
                tabla_afectada="usuarios",
                id_registro_afectado=usuario.id_usuario,
                objeto_afectado=usuario.username,
                descripcion=f"Usuario creado: {usuario.username}",
                request=request,
                datos_nuevos={"roles": usuario.get_roles(), "estado": usuario.estado_acceso},
            )
            messages.success(request, f"Usuario {usuario.username} creado correctamente.")
            return redirect("accounts:usuarios_lista")
        return render(request, self.template_name, {
            "persona_form": persona_form,
            "usuario_form": usuario_form,
            "titulo": "Nuevo usuario",
        })


class UsuarioEditarView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]
    template_name = "accounts/usuario_form.html"

    def get(self, request, pk):
        usuario = get_object_or_404(Usuario.objects.select_related("id_persona"), pk=pk)
        return render(request, self.template_name, {
            "persona_form": PersonaBaseForm(instance=usuario.id_persona, prefix="persona"),
            "usuario_form": UsuarioForm(instance=usuario, prefix="usuario"),
            "usuario_obj": usuario,
            "titulo": f"Editar usuario {usuario.username}",
        })

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario.objects.select_related("id_persona"), pk=pk)
        datos_anteriores = {
            "username": usuario.username,
            "estado": usuario.estado_acceso,
            "roles": usuario.get_roles(),
        }
        persona_form = PersonaBaseForm(
            data=request.POST,
            instance=usuario.id_persona,
            prefix="persona",
        )
        usuario_form = UsuarioForm(data=request.POST, instance=usuario, prefix="usuario")
        if persona_form.is_valid() and usuario_form.is_valid():
            with transaction.atomic():
                persona_form.save()
                usuario = usuario_form.save()

            Bitacora.registrar(
                usuario=request.user,
                modulo="accounts",
                accion="edicion_usuario",
                tabla_afectada="usuarios",
                id_registro_afectado=usuario.id_usuario,
                objeto_afectado=usuario.username,
                descripcion=f"Usuario editado: {usuario.username}",
                request=request,
                datos_anteriores=datos_anteriores,
                datos_nuevos={
                    "username": usuario.username,
                    "estado": usuario.estado_acceso,
                    "roles": usuario.get_roles(),
                },
            )
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("accounts:usuarios_lista")
        return render(request, self.template_name, {
            "persona_form": persona_form,
            "usuario_form": usuario_form,
            "usuario_obj": usuario,
            "titulo": f"Editar usuario {usuario.username}",
        })


class UsuarioDesactivarView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        if usuario.pk == request.user.pk:
            messages.error(request, "No puedes desactivar tu propio usuario.")
            return redirect("accounts:usuarios_lista")
        estado_anterior = usuario.estado_acceso
        usuario.estado_acceso = Usuario.ESTADO_INACTIVO
        usuario.save(update_fields=["estado_acceso", "fecha_actualizacion"])
        Bitacora.registrar(
            usuario=request.user,
            modulo="accounts",
            accion="desactivacion_usuario",
            tabla_afectada="usuarios",
            id_registro_afectado=usuario.id_usuario,
            objeto_afectado=usuario.username,
            descripcion=f"Usuario desactivado logicamente: {usuario.username}",
            request=request,
            datos_anteriores={"estado": estado_anterior},
            datos_nuevos={"estado": usuario.estado_acceso},
        )
        messages.success(request, f"Usuario {usuario.username} desactivado.")
        return redirect("accounts:usuarios_lista")


class UsuarioActivarView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        estado_anterior = usuario.estado_acceso
        usuario.estado_acceso = Usuario.ESTADO_ACTIVO
        usuario.save(update_fields=["estado_acceso", "fecha_actualizacion"])
        Bitacora.registrar(
            usuario=request.user,
            modulo="accounts",
            accion="activacion_usuario",
            tabla_afectada="usuarios",
            id_registro_afectado=usuario.id_usuario,
            objeto_afectado=usuario.username,
            descripcion=f"Usuario activado: {usuario.username}",
            request=request,
            datos_anteriores={"estado": estado_anterior},
            datos_nuevos={"estado": usuario.estado_acceso},
        )
        messages.success(request, f"Usuario {usuario.username} activado.")
        return redirect("accounts:usuarios_lista")


class UsuarioResetPasswordView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]
    template_name = "accounts/usuario_reset_password.html"

    def get(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        return render(request, self.template_name, {
            "form": AdminResetPasswordForm(),
            "usuario_obj": usuario,
        })

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        form = AdminResetPasswordForm(data=request.POST)
        if form.is_valid():
            usuario.set_password(form.cleaned_data["password_nueva"])
            usuario.save(update_fields=["password_hash", "fecha_actualizacion"])
            Bitacora.registrar(
                usuario=request.user,
                modulo="accounts",
                accion="reset_password",
                tabla_afectada="usuarios",
                id_registro_afectado=usuario.id_usuario,
                objeto_afectado=usuario.username,
                descripcion=f"Contrasena reseteada para {usuario.username}",
                request=request,
            )
            messages.success(request, "Contrasena reseteada correctamente.")
            return redirect("accounts:usuarios_lista")
        return render(request, self.template_name, {
            "form": form,
            "usuario_obj": usuario,
        })


class RolListView(RolRequeridoMixin, ListView):
    roles_permitidos = ["administrador"]
    template_name = "accounts/roles_lista.html"
    context_object_name = "roles"
    queryset = Rol.objects.order_by("nombre")


class RolCrearView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]
    template_name = "accounts/rol_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RolForm(), "titulo": "Nuevo rol"})

    def post(self, request):
        form = RolForm(data=request.POST)
        if form.is_valid():
            rol = form.save()
            Bitacora.registrar(
                usuario=request.user,
                modulo="accounts",
                accion="creacion_rol",
                tabla_afectada="roles",
                id_registro_afectado=rol.id_rol,
                objeto_afectado=rol.nombre,
                descripcion=f"Rol creado: {rol.nombre}",
                request=request,
            )
            messages.success(request, "Rol creado correctamente.")
            return redirect("accounts:roles_lista")
        return render(request, self.template_name, {"form": form, "titulo": "Nuevo rol"})


class RolEditarView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]
    template_name = "accounts/rol_form.html"

    def get(self, request, pk):
        rol = get_object_or_404(Rol, pk=pk)
        return render(request, self.template_name, {
            "form": RolForm(instance=rol),
            "rol": rol,
            "titulo": f"Editar rol {rol.nombre}",
        })

    def post(self, request, pk):
        rol = get_object_or_404(Rol, pk=pk)
        estado_anterior = rol.estado_rol
        form = RolForm(data=request.POST, instance=rol)
        if form.is_valid():
            rol = form.save()
            Bitacora.registrar(
                usuario=request.user,
                modulo="accounts",
                accion="edicion_rol",
                tabla_afectada="roles",
                id_registro_afectado=rol.id_rol,
                objeto_afectado=rol.nombre,
                descripcion=f"Rol editado: {rol.nombre}",
                request=request,
                datos_anteriores={"estado": estado_anterior},
                datos_nuevos={"estado": rol.estado_rol},
            )
            messages.success(request, "Rol actualizado correctamente.")
            return redirect("accounts:roles_lista")
        return render(request, self.template_name, {
            "form": form,
            "rol": rol,
            "titulo": f"Editar rol {rol.nombre}",
        })


class RolDesactivarView(RolRequeridoMixin, View):
    roles_permitidos = ["administrador"]

    def post(self, request, pk):
        rol = get_object_or_404(Rol, pk=pk)
        if Usuario.normalizar_nombre_rol(rol.nombre) == "administrador":
            messages.error(request, "El rol administrador no puede desactivarse desde el panel.")
            return redirect("accounts:roles_lista")
        estado_anterior = rol.estado_rol
        rol.estado_rol = Rol.ESTADO_INACTIVO
        rol.save(update_fields=["estado_rol"])
        Bitacora.registrar(
            usuario=request.user,
            modulo="accounts",
            accion="desactivacion_rol",
            tabla_afectada="roles",
            id_registro_afectado=rol.id_rol,
            objeto_afectado=rol.nombre,
            descripcion=f"Rol desactivado logicamente: {rol.nombre}",
            request=request,
            datos_anteriores={"estado": estado_anterior},
            datos_nuevos={"estado": rol.estado_rol},
        )
        messages.success(request, "Rol desactivado.")
        return redirect("accounts:roles_lista")
