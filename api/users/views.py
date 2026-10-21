from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin

User = get_user_model()

# httponly: JS do navegador não acessa o cookie (proteção contra XSS)
# secure: só envia o cookie em HTTPS (desativar só em dev local sem HTTPS)
# samesite="Lax": mitiga CSRF básico
COOKIE_KWARGS = dict(httponly=True, secure=not settings.DEBUG, samesite="Lax") #quando tiver o banco de dados pronto, voltar o secure= para True. Então ficará secure=True


def serialize_user(user):
    return {"id": user.id_po, "nome": user.nome, "email": user.email, "is_admin": user.is_staff}

def serialize_user_admin(user):
    return {
        "id": user.id_po,
        "nome": user.nome,
        "email": user.email,
        "is_active": user.is_active,
        "is_admin": user.is_staff,
        "excluido_em": user.excluido_em,
    }


def revogar_sessoes(user):
    # Invalida no servidor todos os refresh tokens já emitidos para o usuário,
    # para que nenhuma sessão antiga consiga renovar o acesso.
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


# Limita requisições anônimas a 5 tentativas por minuto por IP
class LoginThrottle(AnonRateThrottle):
    rate = '5/min'

class LoginView(APIView):
    authentication_classes = []
    permission_classes = []  # login tem que ser acessível sem estar autenticado
    throttle_classes = [LoginThrottle]

    def post(self, request):
        email = request.data.get("email")
        senha = request.data.get("senha")
        if not email or not senha:
            return Response({"detail": "E-mail e senha são obrigatórios."}, status=400)

        user = authenticate(request, username=email, password=senha)
        if user is None or user.excluido_em is not None:
            return Response({"detail": "Credenciais inválidas."}, status=401)

        refresh = RefreshToken.for_user(user)
        response = Response(serialize_user(user), status=200)
        response.set_cookie("access_token", str(refresh.access_token), **COOKIE_KWARGS)
        response.set_cookie("refresh_token", str(refresh), **COOKIE_KWARGS)
        get_token(request)  # faz o Django emitir o cookie csrftoken nessa resposta
        return response


class LogoutView(APIView):

    authentication_classes = []
    permission_classes = []

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


class AdminUserListView(APIView):
    permission_classes = [IsAdmin]  # só o admin acessa

    def get(self, request):
        queryset = User.objects.all().order_by("nome")

        if request.query_params.get("incluir_excluidos", "").lower() not in ["true", "1"]:
            queryset = queryset.filter(excluido_em__isnull=True)

        # Permite filtrar por ?is_active=true ou ?is_active=false
        is_active_param = request.query_params.get("is_active")
        if is_active_param is not None:
            if is_active_param.lower() in ["true", "1"]:
                queryset = queryset.filter(is_active=True)
            elif is_active_param.lower() in ["false", "0"]:
                queryset = queryset.filter(is_active=False)

        dados = [serialize_user_admin(u) for u in queryset]
        return Response(dados, status=200)


class AdminUserDetailView(APIView):

    permission_classes = [IsAdmin]

    def _alvo(self, request, id_po):
        # Logins já excluídos se comportam como inexistentes (404).
        alvo = get_object_or_404(User, pk=id_po, excluido_em__isnull=True)
        if alvo.pk == request.user.pk:
            return None  # o admin não mexe no próprio login (evita ficar sem nenhum admin)
        return alvo

    def patch(self, request, id_po):
        alvo = self._alvo(request, id_po)
        if alvo is None:
            return Response({"detail": "Você não pode alterar o estado do próprio login."}, status=403)

        novo_estado = request.data.get("is_active")
        if not isinstance(novo_estado, bool):
            return Response({"detail": "O campo 'is_active' (true ou false) é obrigatório."}, status=400)

        with transaction.atomic():
            alvo.is_active = novo_estado
            alvo.save(update_fields=["is_active"])
            if not novo_estado:
                revogar_sessoes(alvo)

        return Response(serialize_user_admin(alvo), status=200)

    def delete(self, request, id_po):
        alvo = self._alvo(request, id_po)
        if alvo is None:
            return Response({"detail": "Você não pode excluir o próprio login."}, status=403)

        with transaction.atomic():
            alvo.is_active = False
            alvo.excluido_em = timezone.now()
            alvo.save(update_fields=["is_active", "excluido_em"])
            revogar_sessoes(alvo)

        return Response(status=204)