"""apps/accounts/urls.py"""
from django.urls import path
from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("cambiar-password/", views.CambiarPasswordView.as_view(), name="cambiar_password"),
    path("usuarios/", views.UsuarioListView.as_view(), name="usuarios_lista"),
    path("usuarios/nuevo/", views.UsuarioCrearView.as_view(), name="usuarios_crear"),
    path("usuarios/<int:pk>/editar/", views.UsuarioEditarView.as_view(), name="usuarios_editar"),
    path("usuarios/<int:pk>/desactivar/", views.UsuarioDesactivarView.as_view(), name="usuarios_desactivar"),
    path("usuarios/<int:pk>/activar/", views.UsuarioActivarView.as_view(), name="usuarios_activar"),
    path("usuarios/<int:pk>/reset-password/", views.UsuarioResetPasswordView.as_view(), name="usuarios_reset_password"),
    path("roles/", views.RolListView.as_view(), name="roles_lista"),
    path("roles/nuevo/", views.RolCrearView.as_view(), name="roles_crear"),
    path("roles/<int:pk>/editar/", views.RolEditarView.as_view(), name="roles_editar"),
    path("roles/<int:pk>/desactivar/", views.RolDesactivarView.as_view(), name="roles_desactivar"),
]
