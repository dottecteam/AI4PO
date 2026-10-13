from django.urls import path

from .views import ChatView
from .views_conversas import ConversaDetalheView, ConversaListView
from .views_export import ConversaExportarPDFView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("conversas/", ConversaListView.as_view(), name="conversa-list"),
    path("conversas/<int:conversa_id>/mensagens/", ConversaDetalheView.as_view(), name="conversa-detalhe"),
    path("conversas/<int:conversa_id>/exportar-pdf/", ConversaExportarPDFView.as_view(), name="conversa-exportar-pdf"),
]