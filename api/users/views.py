from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

# httponly: JS do navegador não acessa o cookie (proteção contra XSS)
# secure: só envia o cookie em HTTPS (desativar só em dev local sem HTTPS)
# samesite="Lax": mitiga CSRF básico
COOKIE_KWARGS = dict(httponly=True, secure=False, samesite="Lax") #quando tiver o banco de dados pronto, voltar o secure= para True. Então ficará secure=True


def serialize_user(user):
    # dados públicos do usuário — nunca inclua password/hash aqui
    return {"id": user.id_po, "nome": user.nome, "email": user.email}


class LoginView(APIView):
    permission_classes = []  # login tem que ser acessível sem estar autenticado

    def post(self, request):
        email = request.data.get("email")
        senha = request.data.get("senha")
        if not email or not senha:
            return Response({"detail": "E-mail e senha são obrigatórios."}, status=400)

        # authenticate() usa USERNAME_FIELD="email" definido no model
        user = authenticate(request, username=email, password=senha)
        if user is None:
            return Response({"detail": "Credenciais inválidas."}, status=401)

        refresh = RefreshToken.for_user(user)  # gera o par access + refresh
        response = Response(serialize_user(user), status=200)
        response.set_cookie("access_token", str(refresh.access_token), **COOKIE_KWARGS)
        response.set_cookie("refresh_token", str(refresh), **COOKIE_KWARGS)
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
        return Response(serialize_user(request.user))