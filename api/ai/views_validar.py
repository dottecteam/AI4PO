from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.authentication import CookieJWTAuthentication
from .checklist import resumo_validacao

# O checklist compara textos com SequenceMatcher (custo quadrático), então limitamos o tamanho do corpo para evitar requisições abusivas.
TAMANHO_MAX_BYTES = 256 * 1024


class ValidarEspecificacaoView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        try:
            tamanho = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            tamanho = 0
        if tamanho > TAMANHO_MAX_BYTES:
            return Response({"error": "Especificação grande demais."}, status=413)

        dados = request.data
        if not isinstance(dados, dict) or not isinstance(dados.get("epicos"), list):
            return Response(
                {"error": "Envie um objeto JSON com a chave 'epicos' (lista)."},
                status=400,
            )

        return Response(resumo_validacao(dados))