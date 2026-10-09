from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from weasyprint import HTML

from users.authentication import CookieJWTAuthentication
from .models import Conversa
from .pdf_markdown import md_para_html


class ConversaExportarPDFView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, conversa_id):
        conversa = get_object_or_404(Conversa, pk=conversa_id, usuario_po=request.user)
        mensagens = list(conversa.mensagens.all())
        for m in mensagens:
            if m.papel == "assistant":
                m.html = md_para_html(m.conteudo)

        html = render_to_string("ai/conversa_pdf.html", {
            "conversa": conversa,
            "mensagens": mensagens,
            "agora": timezone.now(),
        })
        pdf = HTML(string=html).write_pdf()

        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="conversa-{conversa.pk}.pdf"'
        return resp