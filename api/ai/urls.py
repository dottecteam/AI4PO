from django.urls import path

from .views import SimilarityCheckView, ChatView
from .views_busca import BuscaSemanticaView
from .views_conversas import ConversaDetalheView, ConversaListView
from .views_export import ConversaExportarPDFView
from .views_validar import ValidarEspecificacaoView
from .views_reformatar import ReformatarRequisitoView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("busca/", BuscaSemanticaView.as_view(), name="busca-semantica"),
    path("conversas/", ConversaListView.as_view(), name="conversa-list"),
    path("conversas/<int:conversa_id>/mensagens/", ConversaDetalheView.as_view(), name="conversa-detalhe"),
    path("conversas/<int:conversa_id>/exportar-pdf/", ConversaExportarPDFView.as_view(), name="conversa-exportar-pdf"),
    path("validar/", ValidarEspecificacaoView.as_view(), name="validar-especificacao"),
    path("reformatar/", ReformatarRequisitoView.as_view(), name="reformatar-requisito"),
    path("similarity/", SimilarityCheckView.as_view(), name="similarity-check"),
]
