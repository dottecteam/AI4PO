from django.urls import path

from .views import DocumentoUploadView
from projects.views import ProjetoListCreateView, ProjetoDataView

urlpatterns = [
    path("projects/<int:project_id>/documents/",DocumentoUploadView.as_view(),name="document-upload",),
    path('projetos/', ProjetoListCreateView.as_view(), name = 'projeto-list-create'),
    path('projetos/<int:pk>/', ProjetoDataView.as_view(), name = 'projeto_detail')
]