from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from users.models import UsuarioPO
from users.views import LoginThrottle

LoginThrottle.rate = '1000/min'  # o throttle real (5/min) atrapalha testes que logam várias vezes

BASE = "/api/auth/"


def logar(email, senha="senha123"):
    c = APIClient(enforce_csrf_checks=True)
    r = c.post(BASE + "login/", {"email": email, "senha": senha}, format="json")
    return c, r


def csrf(c):
    return {"HTTP_X_CSRFTOKEN": c.cookies["csrftoken"].value}


class PerfilTests(TestCase):
    """Task #10-7 — tela de perfil: dados gerais (GET /me/) e logoff (POST /logout/)."""

    def setUp(self):
        cache.clear()
        self.po = UsuarioPO.objects.create_user("po@x.com", "Maria PO", "senha123")
        self.admin = UsuarioPO.objects.create_user("admin@x.com", "Admin", "senha123")
        self.admin.is_staff = True
        self.admin.save()

    def test_me_devolve_dados_gerais_sem_campos_sensiveis(self):
        c, r = logar("po@x.com")
        self.assertEqual(r.status_code, 200)
        dados = c.get(BASE + "me/").json()
        self.assertEqual(dados, {"id": self.po.id_po, "nome": "Maria PO", "email": "po@x.com", "is_admin": False})
        for proibido in ("password", "senha", "is_staff", "excluido_em"):
            self.assertNotIn(proibido, dados)

    def test_me_indica_perfil_de_admin(self):
        c, _ = logar("admin@x.com")
        self.assertTrue(c.get(BASE + "me/").json()["is_admin"])

    def test_me_exige_login(self):
        self.assertEqual(APIClient().get(BASE + "me/").status_code, 401)

    def test_logoff_encerra_a_sessao_e_invalida_o_refresh_token(self):
        c, _ = logar("po@x.com")
        self.assertEqual(c.get(BASE + "me/").status_code, 200)
        self.assertEqual(OutstandingToken.objects.filter(user=self.po).count(), 1)

        r = c.post(BASE + "logout/", **csrf(c))
        self.assertEqual(r.status_code, 204)

        # cookies de sessão apagados na resposta
        self.assertEqual(r.cookies["access_token"].value, "")
        self.assertEqual(r.cookies["refresh_token"].value, "")
        # refresh token invalidado no servidor
        self.assertTrue(BlacklistedToken.objects.filter(token__user=self.po).exists())
        # e, sem os cookies, a sessão não existe mais
        self.assertEqual(c.get(BASE + "me/").status_code, 401)

    def test_logoff_nao_derruba_a_sessao_de_outro_usuario(self):
        c1, _ = logar("po@x.com")
        c2, _ = logar("admin@x.com")
        self.assertEqual(c1.post(BASE + "logout/", **csrf(c1)).status_code, 204)
        self.assertEqual(c2.get(BASE + "me/").status_code, 200)

    def test_logoff_sem_estar_logado_nao_quebra(self):
        r = APIClient(enforce_csrf_checks=True).post(BASE + "logout/")
        self.assertEqual(r.status_code, 204)

    def test_pode_logar_de_novo_depois_do_logoff(self):
        c, _ = logar("po@x.com")
        c.post(BASE + "logout/", **csrf(c))
        c2, r = logar("po@x.com")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(c2.get(BASE + "me/").status_code, 200)