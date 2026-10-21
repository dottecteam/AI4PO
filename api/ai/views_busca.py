import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.indexing import FalhaDeEmbeddingError
from ai.retrieval import buscar_trechos
from projects.models import Projeto
from users.authentication import CookieJWTAuthentication

logger = logging.getLogger(__name__)

LIMITE_MAXIMO = 10


class BuscaSemanticaView(APIView):
    """POST /api/busca/ — busca semântica no histórico indexado, com origem dos trechos.

    Corpo: {"consulta": "texto", "projeto_id": 3 (opcional), "limite": 4 (opcional, até 10)}
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        consulta = (request.data.get("consulta") or "").strip()
        if not consulta:
            return Response({"error": "A consulta é obrigatória."}, status=status.HTTP_400_BAD_REQUEST)

        projeto_id = request.data.get("projeto_id") or None
        if projeto_id is not None:
            try:
                projeto_id = int(projeto_id)
            except (TypeError, ValueError):
                return Response({"error": "projeto_id inválido."}, status=status.HTTP_400_BAD_REQUEST)
            # 404 também para projeto de outro PO: não revela que ele existe
            get_object_or_404(Projeto, pk=projeto_id, usuario_po=request.user)

        limite = request.data.get("limite")
        if limite is not None:
            try:
                limite = max(1, min(int(limite), LIMITE_MAXIMO))
            except (TypeError, ValueError):
                return Response({"error": "limite inválido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultados = buscar_trechos(consulta, request.user, projeto_id=projeto_id, limite=limite)
        except FalhaDeEmbeddingError as erro:
            logger.error("Falha ao gerar vetor da consulta: %s", erro)
            return Response(
                {"error": "Serviço de embeddings indisponível no momento."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"consulta": consulta, "total": len(resultados), "resultados": resultados})