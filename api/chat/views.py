from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML

from .models import Conversa, Mensagem


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conversa_id = request.data.get("conversa_id")
        texto = request.data["mensagem"]

        if conversa_id:
            conversa = get_object_or_404(Conversa, pk=conversa_id, usuario=request.user)
        else:
            conversa = Conversa.objects.create(usuario=request.user, titulo=texto[:60])

        Mensagem.objects.create(conversa=conversa, role="user", conteudo=texto)

        resposta = chamar_ollama(texto)

        Mensagem.objects.create(conversa=conversa, role="assistant", conteudo=resposta)

        return Response({"conversa_id": conversa.id, "resposta": resposta})


class ConversaExportarPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        conversa = get_object_or_404(Conversa, pk=pk, usuario=request.user)
        mensagens = conversa.mensagens.all()

        html = render_to_string("chat/conversa_pdf.html", {
            "conversa": conversa,
            "mensagens": mensagens,
            "agora": timezone.now(),
        })
        pdf = HTML(string=html).write_pdf()

        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="conversa-{conversa.pk}.pdf"'
        return resp