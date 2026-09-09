# Estratégia de token de autenticação (JWT)

1\. Login Next.js (envia usuário e senha) →

2\. Django valida (confere credenciais) →

3\. Emite JWT (access \+ refresh token) →

4\. Cliente guarda o token (cookie httpOnly) →

5\. Requisição à API (Authorization: Bearer token) →

6\. Django verifica assinatura (sem consultar sessão no banco) →

7\. Acesso liberado (resposta da API)

## **Biblioteca**

Para JWT com Django, a escolha mais fácil e segura é:

***`- djangorestframework-simplejwt`***

* Integra direto com Django REST Framework (DRF).  
* Fácil de configurar (poucas linhas de `settings.py`).  
* Suporta access token \+ refresh token, expiração configurável, blacklist de tokens (com app extra `token_blacklist`).  
* Mantida ativamente, bastante usada em produção, não é "gambiarra".

Instalação básica:

*pip install djangorestframework djangorestframework-simplejwt*

Exemplos:

\# settings.py  
INSTALLED\_APPS \= \[  
    ...  
    'rest\_framework',  
    'rest\_framework\_simplejwt',  
\]

REST\_FRAMEWORK \= {  
    'DEFAULT\_AUTHENTICATION\_CLASSES': (  
        'rest\_framework\_simplejwt.authentication.JWTAuthentication',  
    ),  
}

\# urls.py  
from rest\_framework\_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns \= \[  
    path('api/token/', TokenObtainPairView.as\_view()),  
    path('api/token/refresh/', TokenRefreshView.as\_view()),  
\]

## **Justificativa da escolha (JWT vs sessão)**

Optamos por JWT em vez de sessão porque o frontend (Next.js/React) é separado do backend (Django), rodando em domínio/porta diferente. Autenticação por sessão depende de cookies vinculados ao domínio do servidor, o que exigiria lidar com complexidade extra de CORS e configuração de cookies cross-site. Com JWT, o cliente simplesmente guarda o token e o envia no header `Authorization`, sem essa dependência.

**Trade-off / desvantagem**

Por ser stateless, o JWT não permite que o servidor "esqueça" um token antes da sua expiração. Isso significa que, para revogar acesso antecipadamente (logout forçado, usuário banido, etc.), é necessário manter uma blacklist de tokens, resolvido pelo app `token_blacklist` do `djangorestframework-simplejwt`, que já faz parte da biblioteca escolhida.

**Armazenamento do token no cliente**

O token será armazenado em **cookie httpOnly** no Next.js, e não em memória ou localStorage. Essa escolha reduz a superfície de ataque contra XSS, já que o JavaScript no navegador não tem acesso direto ao cookie. Como contrapartida, é necessário proteger as rotas contra CSRF (ex: usando `SameSite=Strict` ou `Lax` no cookie).

