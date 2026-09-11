from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    A lib padrão do simplejwt só lê o token do header Authorization.
    Como decidimos usar cookie httpOnly, sobrescreve para ler o
    token do cookie 'access_token' em cada requisição autenticada.
    """
    def authenticate(self, request):
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None  # sem cookie = requisição anônima, não é erro
        validated_token = self.get_validated_token(raw_token)  # valida assinatura/expiração
        return self.get_user(validated_token), validated_token