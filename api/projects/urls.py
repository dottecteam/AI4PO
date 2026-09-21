from django.urls import path
from projects.views import ProjetoListCreateView, ProjetoDataView

urlpatterns = [
    path('projetos/', ProjetoListCreateView.as_view(), name = 'projeto-list-create'),
    path('projetos/<int:pk>/', ProjetoDataView.as_view(), name = 'projeto_detail')
]