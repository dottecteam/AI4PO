from django.urls import path

from .views import DocumentoUploadView, DocumentoListView, DocumentoReprocessarView
from projects.views import ProjetoListCreateView, ProjetoDataView

urlpatterns = [
    path("projects/<int:project_id>/documents/", DocumentoListView.as_view(), name="document-list"),
    path("projects/<int:project_id>/documents/upload/", DocumentoUploadView.as_view(), name="document-upload"),
    path("projects/<int:project_id>/documents/<int:document_id>/reprocess/", DocumentoReprocessarView.as_view(), name="document-reprocess"),
    path('projetos/', ProjetoListCreateView.as_view(), name='projeto-list-create'),
    path('projetos/<int:pk>/', ProjetoDataView.as_view(), name='projeto_detail')
]