# users/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import CSRFCheck
from rest_framework import exceptions

def enforce_csrf(request):
    """Força a validação do token CSRF nativa do Django."""
    check = CSRFCheck(request)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f"Falha de CSRF: {reason}")

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None  # sem cookie = requisição anônima
        
        validated_token = self.get_validated_token(raw_token)
        
        # Valida o CSRF para requisições de mutação de estado (POST, PUT, PATCH, DELETE)
        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            enforce_csrf(request)
            
        return self.get_user(validated_token), validated_token