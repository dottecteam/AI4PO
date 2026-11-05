from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.models import Documento, Projeto
from users.authentication import CookieJWTAuthentication

from .models import Conversa, MensagemChat


class ResumoDashboardView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projetos = Projeto.objects.all()
        documentos = Documento.objects.all()
        conversas = Conversa.objects.all()
        validacoes = MensagemChat.objects.filter(
            papel="assistant", metadata__has_key="validacao"
        )

        if not getattr(request.user, "is_admin", False):
            projetos = projetos.filter(usuario_po=request.user)
            documentos = documentos.filter(projeto__usuario_po=request.user)
            conversas = conversas.filter(usuario_po=request.user)
            validacoes = validacoes.filter(conversa__usuario_po=request.user)

        docs = documentos.aggregate(
            total=Count("id"),
            processados=Count("id", filter=Q(estado="processado")),
            processando=Count("id", filter=Q(estado="processando")),
            com_erro=Count("id", filter=Q(estado="erro")),
        )
        docs["percentual_indexado"] = (
            round(docs["processados"] * 100 / docs["total"]) if docs["total"] else 0
        )

        return Response({
            "projetos": projetos.count(),
            "documentos": docs,
            "conversas": conversas.count(),
            "validacoes": validacoes.count(),
        })