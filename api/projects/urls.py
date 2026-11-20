from django.urls import path

from .views import DocumentoUploadView, DocumentoListView, DocumentoReprocessarView, DocumentoDeleteView
from projects.views import ProjetoListCreateView, ProjetoDataView
from projects.views import ParticipacaoListCreateView, ParticipacaoDataView
from projects.views import ProfissionalListView, ProfissionalPerfilView, MeuPerfilProfissionalView

urlpatterns = [
    path("projects/<int:project_id>/documents/", DocumentoListView.as_view(), name="document-list"),
    path("projects/<int:project_id>/documents/upload/", DocumentoUploadView.as_view(), name="document-upload"),
    path("projects/<int:project_id>/documents/<int:document_id>/reprocess/", DocumentoReprocessarView.as_view(), name="document-reprocess"),
    path("projects/<int:project_id>/documents/<int:document_id>/", DocumentoDeleteView.as_view(), name="document-delete"),
    path('projetos/', ProjetoListCreateView.as_view(), name='projeto-list-create'),
    path('projetos/<int:pk>/', ProjetoDataView.as_view(), name='projeto_detail'),
    path("participacoes/", ParticipacaoListCreateView.as_view(), name="participacao-list-create"),
    path("participacoes/<int:pk>/", ParticipacaoDataView.as_view(), name="participacao-detail"),
    path("profissionais/", ProfissionalListView.as_view(), name="profissional-list"),
    path("profissionais/me/", MeuPerfilProfissionalView.as_view(), name="profissional-me"),
    path("profissionais/<int:pk>/", ProfissionalPerfilView.as_view(), name="profissional-perfil"),
]