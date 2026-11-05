from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.authentication import CookieJWTAuthentication

from .models import ACOES, Atividade


class AtividadesRecentesView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limite = max(1, min(int(request.query_params.get("limite", 5)), 50))
        except ValueError:
            limite = 5

        qs = Atividade.objects.all()
        qs = qs.filter(usuario=request.user)

        return Response([
            {
                "id": a.id,
                "usuario": a.usuario_nome,
                "texto": ACOES.get(a.acao, a.acao),
                "alvo": a.alvo,
                "criado_em": a.criado_em.isoformat(),
            }
            for a in qs[:limite]
        ])