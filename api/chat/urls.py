from django.urls import path
from .views import ChatView, ConversaExportarPDFView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("conversas/<int:pk>/exportar-pdf/", ConversaExportarPDFView.as_view(), name="conversa-exportar-pdf"),
]