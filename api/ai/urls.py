from django.urls import path

from .views import ChatView
from .views_conversas import ConversaDetalheView, ConversaListView
from .views_reformatar import ReformatarRequisitoView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("conversas/", ConversaListView.as_view(), name="conversa-list"),
    path("conversas/<int:conversa_id>/mensagens/", ConversaDetalheView.as_view(), name="conversa-detalhe"),
    path("reformatar/", ReformatarRequisitoView.as_view(), name="reformatar-requisito"),
]