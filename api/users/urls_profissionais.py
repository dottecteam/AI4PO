from django.urls import path

from .views_profissionais import BuscaProfissionaisView

urlpatterns = [
    path("profissionais/busca/", BuscaProfissionaisView.as_view(), name="profissionais-busca"),
]