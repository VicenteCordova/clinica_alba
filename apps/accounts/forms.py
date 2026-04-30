"""
apps/accounts/forms.py
"""
from django import forms
from django.contrib.auth.hashers import make_password
from apps.accounts.models import Usuario, Rol, UsuarioRol
from apps.core.forms import AlbaFormMixin



class LoginForm(AlbaFormMixin, forms.Form):
    username = forms.CharField(
        label="Usuario",
        max_length=50,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nombre de usuario", "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Contraseña"}
        ),
    )

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username")
        password = cleaned.get("password")
        if username and password:
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError(
                    "Usuario o contraseña incorrectos, o la cuenta está bloqueada."
                )
            self._usuario_autenticado = user
        return cleaned

    def get_usuario(self):
        return getattr(self, "_usuario_autenticado", None)


class CambiarPasswordForm(AlbaFormMixin, forms.Form):
    password_actual = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password_nueva = forms.CharField(
        label="Nueva contraseña",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password_confirmacion = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def __init__(self, usuario, *args, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)

    def clean_password_actual(self):
        actual = self.cleaned_data["password_actual"]
        if not self.usuario.check_password(actual):
            raise forms.ValidationError("La contraseña actual es incorrecta.")
        return actual

    def clean(self):
        cleaned = super().clean()
        nueva = cleaned.get("password_nueva")
        confirmacion = cleaned.get("password_confirmacion")
        if nueva and confirmacion and nueva != confirmacion:
            raise forms.ValidationError(
                "La nueva contraseña y su confirmación no coinciden."
            )
        return cleaned

    def save(self):
        nueva = self.cleaned_data["password_nueva"]
        self.usuario.set_password(nueva)
        self.usuario.save(update_fields=["password_hash"])


class UsuarioForm(AlbaFormMixin, forms.ModelForm):
    """Formulario para crear/editar un usuario."""

    password = forms.CharField(
        label="Contraseña",
        min_length=8,
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text="Dejar en blanco para mantener la contraseña actual.",
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=Rol.objects.filter(estado_rol="activo"),
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        label="Roles",
    )

    class Meta:
        model = Usuario
        fields = ["username", "estado_acceso"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "estado_acceso": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        self.fields["roles"].queryset = Rol.objects.filter(
            estado_rol=Rol.ESTADO_ACTIVO
        ).order_by("nombre")
        if not instance:
            self.fields["password"].required = True
        if instance:
            self.fields["roles"].initial = Rol.objects.filter(
                usuario_roles__id_usuario=instance
            )

    def clean_roles(self):
        roles = self.cleaned_data.get("roles")
        if not roles:
            raise forms.ValidationError("Debes seleccionar al menos un rol.")
        return roles

    def aplicar_flags_admin(self, usuario):
        roles = [
            Usuario.normalizar_nombre_rol(rol.nombre)
            for rol in self.cleaned_data.get("roles", [])
        ]
        usuario.is_staff = "administrador" in roles
        usuario.is_superuser = "administrador" in roles

    def sync_roles(self, usuario):
        roles = list(self.cleaned_data.get("roles", []))
        roles_actuales = set(
            UsuarioRol.objects.filter(id_usuario=usuario)
            .values_list("rol_id", flat=True)
        )
        roles_nuevos = {rol.pk for rol in roles}

        for rol in roles:
            UsuarioRol.objects.get_or_create(id_usuario=usuario, rol=rol)
        UsuarioRol.objects.filter(
            id_usuario=usuario,
            rol_id__in=roles_actuales - roles_nuevos,
        ).delete()

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            usuario.set_password(password)
        self.aplicar_flags_admin(usuario)
        if commit:
            usuario.save()
            self.sync_roles(usuario)
        return usuario


class RolForm(AlbaFormMixin, forms.ModelForm):
    """Formulario administrativo para crear y editar roles."""

    class Meta:
        model = Rol
        fields = ["nombre", "descripcion", "estado_rol"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
            "estado_rol": forms.Select(attrs={"class": "form-select"}),
        }


class AdminResetPasswordForm(AlbaFormMixin, forms.Form):
    password_nueva = forms.CharField(
        label="Nueva contrasena",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password_confirmacion = forms.CharField(
        label="Confirmar contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned = super().clean()
        nueva = cleaned.get("password_nueva")
        confirmacion = cleaned.get("password_confirmacion")
        if nueva and confirmacion and nueva != confirmacion:
            raise forms.ValidationError("La contrasena y su confirmacion no coinciden.")
        return cleaned
