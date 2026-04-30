"""apps/auditoria/urls.py"""
from django.urls import path
from apps.auditoria import views

app_name = "auditoria"

urlpatterns = [
    path("", views.BitacoraListView.as_view(), name="lista"),
]
