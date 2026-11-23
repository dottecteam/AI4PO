from django.urls import path

from .views_funcionarios import CompetenciaDetailView, CompetenciaListView, ProfissionalListCreateView
from .views_profissionais import BuscaProfissionaisView

urlpatterns = [
    path("competencias/", CompetenciaListView.as_view(), name="competencias-lista"),
    path("competencias/<int:pk>/", CompetenciaDetailView.as_view(), name="competencias-detalhe"),
    path("profissionais/", ProfissionalListCreateView.as_view(), name="profissionais-lista"),
    path("profissionais/busca/", BuscaProfissionaisView.as_view(), name="profissionais-busca"),
]