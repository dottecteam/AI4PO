from django.urls import path

from .views import SimilarityCheckView, ChatView
from .views_busca import BuscaSemanticaView
from .views_conversas import ConversaDetalheView, ConversaListView, ConversaExcluirView
from .views_export import ConversaExportarPDFView
from .views_validar import ValidarEspecificacaoView
from .views_reformatar import ReformatarRequisitoView
from .views_grafo import GrafoStatusView, GrafoDadosView, GrafoPosicoesView
from .views_dashboard import ResumoDashboardView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("busca/", BuscaSemanticaView.as_view(), name="busca-semantica"),
    path("conversas/", ConversaListView.as_view(), name="conversa-list"),
    path("conversas/<int:conversa_id>/mensagens/", ConversaDetalheView.as_view(), name="conversa-detalhe"),
    path("conversas/<int:conversa_id>/exportar-pdf/", ConversaExportarPDFView.as_view(), name="conversa-exportar-pdf"),
    path("conversas/<int:conversa_id>/", ConversaExcluirView.as_view(), name="conversa-excluir"),
    path("validar/", ValidarEspecificacaoView.as_view(), name="validar-especificacao"),
    path("reformatar/", ReformatarRequisitoView.as_view(), name="reformatar-requisito"),
    path("similarity/", SimilarityCheckView.as_view(), name="similarity-check"),
    path("grafo/status/<int:documento_id>/", GrafoStatusView.as_view(), name="grafo-status"),
    path("grafo/dados/", GrafoDadosView.as_view(), name="grafo-dados"),
    path("grafo/posicoes/", GrafoPosicoesView.as_view(), name="grafo-posicoes"),
    path("dashboard/resumo/", ResumoDashboardView.as_view(), name="dashboard-resumo"),
]
