from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from users.authentication import CookieJWTAuthentication

from .models import Conversa
from .reformatar import (
    TIPOS_VALIDOS,
    ReformatacaoError,
    gerar_reformatacao,
    reformatacao_pendente,
    salvar_reformatacao,
)


class ReformatarRequisitoView(APIView):
    """Endpoint explícito de reformatação. O chat principal não depende dele
    (o ChatView decide pelo contexto), mas ele continua útil para testes."""

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mensagem = (request.data.get("mensagem") or "").strip()
        tipo = (request.data.get("tipo") or "pbi").strip().lower()
        ajuste = bool(request.data.get("ajuste"))
        conversa_id = request.data.get("conversa_id")

        if not mensagem:
            return JsonResponse({"error": "O campo 'mensagem' é obrigatório."}, status=400)

        if tipo not in TIPOS_VALIDOS:
            return JsonResponse(
                {"error": f"'tipo' inválido. Use um de: {', '.join(sorted(TIPOS_VALIDOS))}."},
                status=400,
            )

        conversa = None
        if conversa_id:
            conversa = get_object_or_404(Conversa, pk=conversa_id, usuario_po=request.user)

        anterior = None
        if ajuste:
            anterior = reformatacao_pendente(conversa) if conversa else None
            if anterior is None:
                return JsonResponse({"error": "Não há versão anterior para ajustar."}, status=400)

        try:
            resultado = gerar_reformatacao(mensagem, tipo, anterior)
        except ReformatacaoError as erro:
            return JsonResponse({"error": erro.mensagem}, status=erro.status)

        # só cria a conversa depois do sucesso, pra não sobrar conversa vazia
        if conversa is None:
            conversa = Conversa.objects.create(usuario_po=request.user, titulo=mensagem[:60])

        salvar_reformatacao(conversa, mensagem, resultado)

        return JsonResponse(
            {
                "conversa_id": conversa.id,
                "tipo": resultado["tipo"],
                "requisito_original": resultado["original"],
                "requisito_reformatado": resultado["reformatado"],
            }
        )