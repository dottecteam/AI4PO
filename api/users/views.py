from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.throttling import AnonRateThrottle
from django.conf import settings
from .permissions import IsAdmin
from django.contrib.auth import get_user_model

from django.middleware.csrf import get_token

# httponly: JS do navegador não acessa o cookie (proteção contra XSS)
# secure: só envia o cookie em HTTPS (desativar só em dev local sem HTTPS)
# samesite="Lax": mitiga CSRF básico
COOKIE_KWARGS = dict(httponly=True, secure=not settings.DEBUG, samesite="Lax") #quando tiver o banco de dados pronto, voltar o secure= para True. Então ficará secure=True


def serialize_user(user):
    # dados públicos do usuário — nunca inclua password/hash aqui
    return {"id": user.id_po, "nome": user.nome, "email": user.email}

def serialize_user_admin(user):
    # Serialização específica para rotas administrativas de gestão.
    # Expõe dados cadastrais e o estado da conta (is_active / is_admin)
    # para consulta e moderação, sem expor campos sensíveis (como hashes de senha).
    return {
        "id": user.id_po,
        "nome": user.nome,
        "email": user.email,
        "is_active": user.is_active,  # <--- o campo da task
        "is_admin": getattr(user, "is_admin", False),
    }
# Limita requisições anônimas a 5 tentativas por minuto por IP
class LoginThrottle(AnonRateThrottle):
    rate = '5/min'

class LoginView(APIView):
    permission_classes = []  # login tem que ser acessível sem estar autenticado
    throttle_classes = [LoginThrottle]
    
    def post(self, request):
        email = request.data.get("email")
        senha = request.data.get("senha")
        if not email or not senha:
            return Response({"detail": "E-mail e senha são obrigatórios."}, status=400)

        # authenticate() usa USERNAME_FIELD="email" definido no model
        user = authenticate(request, username=email, password=senha)
        if user is None:
            return Response({"detail": "Credenciais inválidas."}, status=401)

        refresh = RefreshToken.for_user(user)
        response = Response(serialize_user(user), status=200)
        response.set_cookie("access_token", str(refresh.access_token), **COOKIE_KWARGS)
        response.set_cookie("refresh_token", str(refresh), **COOKIE_KWARGS)
        get_token(request)  # faz o Django emitir o cookie csrftoken nessa resposta
        return response


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()  # invalida o refresh no servidor
            except TokenError:
                pass  # token já inválido/expirado — segue o logout normalmente
        response = Response(status=204)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]  # só acessa quem tem cookie válido

    def get(self, request):
        get_token(request)
        return Response(serialize_user(request.user))


class AdminOnlyView(APIView):
    permission_classes = [IsAdmin]  # só acessa quem é um admin

    def get(self, request):
        return Response({"mensagem": "Bem-vindo, chefe! Você é um administrador."}) # Teste



User = get_user_model()

class AdminUserListView(APIView):
    permission_classes = [IsAdmin]  # só o admin acessa

    def get(self, request):
        queryset = User.objects.all().order_by("nome")

        # Permite filtrar por ?is_active=true ou ?is_active=false
        is_active_param = request.query_params.get("is_active")
        if is_active_param is not None:
            if is_active_param.lower() in ["true", "1"]:
                queryset = queryset.filter(is_active=True)
            elif is_active_param.lower() in ["false", "0"]:
                queryset = queryset.filter(is_active=False)

        dados = [serialize_user_admin(u) for u in queryset]
        return Response(dados, status=200)