from django.test import TestCase
from rest_framework.test import APIClient
from users.models import UsuarioPO
from projects.models import Projeto, Documento
from django.core.cache import cache
from users.views import LoginThrottle

LoginThrottle.rate = '1000/min'  # o throttle real (5/min) atrapalha testes que logam várias vezes

BASE = "/api/auth/"


def logar(email, senha="senha123"):
    c = APIClient(enforce_csrf_checks=True)
    r = c.post(BASE + "login/", {"email": email, "senha": senha}, format="json")
    return c, r


def csrf(c):
    return {"HTTP_X_CSRFTOKEN": c.cookies["csrftoken"].value}


class GestaoLoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = UsuarioPO.objects.create_user("admin@x.com", "Admin", "senha123")
        self.admin.is_staff = True
        self.admin.save()
        self.po = UsuarioPO.objects.create_user("po@x.com", "PO Um", "senha123")
        self.outro = UsuarioPO.objects.create_user("outro@x.com", "PO Dois", "senha123")
        self.proj = Projeto.objects.create(usuario_po=self.po, titulo="P", descricao="d")
        self.doc = Documento.objects.create(projeto=self.proj, nome="a.md")
        self.ca, r = logar("admin@x.com")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["is_admin"])
        self.url = BASE + f"admin/users/{self.po.id_po}/"

    # ---- #10-2: restrito ao admin ----
    def test_anonimo_nao_acessa(self):
        c = APIClient(enforce_csrf_checks=True)
        self.assertIn(c.patch(self.url, {"is_active": False}, format="json").status_code, (401, 403))
        self.assertIn(c.delete(self.url).status_code, (401, 403))

    def test_nao_admin_recebe_403(self):
        c, r = logar("outro@x.com")
        self.assertFalse(r.json()["is_admin"])
        self.assertEqual(c.patch(self.url, {"is_active": False}, format="json", **csrf(c)).status_code, 403)
        self.assertEqual(c.delete(self.url, **csrf(c)).status_code, 403)
        self.po.refresh_from_db()
        self.assertTrue(self.po.is_active)
        self.assertIsNone(self.po.excluido_em)

    def test_csrf_exigido(self):
        self.assertEqual(self.ca.patch(self.url, {"is_active": False}, format="json").status_code, 403)
        self.assertEqual(self.ca.delete(self.url).status_code, 403)

    # ---- #10-2 + #10-3: desativar / reativar ----
    def test_desativar_bloqueia_login_e_sessao_aberta_e_reativar_restaura(self):
        cpo, r = logar("po@x.com")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(cpo.get(BASE + "me/").status_code, 200)

        r = self.ca.patch(self.url, {"is_active": False}, format="json", **csrf(self.ca))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["is_active"])

        # sessão que já estava aberta cai na hora
        self.assertEqual(cpo.get(BASE + "me/").status_code, 401)
        # e não consegue logar de novo, nem com o cookie velho no navegador
        c2, r2 = logar("po@x.com")
        self.assertEqual(r2.status_code, 401)
        cpo2 = APIClient(enforce_csrf_checks=True)
        cpo2.cookies = cpo.cookies
        self.assertEqual(cpo2.post(BASE + "login/", {"email": "po@x.com", "senha": "senha123"}, format="json").status_code, 401)

        # reativar
        r = self.ca.patch(self.url, {"is_active": True}, format="json", **csrf(self.ca))
        self.assertTrue(r.json()["is_active"])
        c3, r3 = logar("po@x.com")
        self.assertEqual(r3.status_code, 200)

    def test_login_novo_funciona_mesmo_com_cookie_velho_de_outra_conta(self):
        cpo, _ = logar("po@x.com")
        self.ca.patch(self.url, {"is_active": False}, format="json", **csrf(self.ca))
        # o mesmo navegador (cookie velho do PO desativado) loga como outro usuário
        cpo.cookies.pop("csrftoken", None)
        r = cpo.post(BASE + "login/", {"email": "outro@x.com", "senha": "senha123"}, format="json")
        self.assertEqual(r.status_code, 200)

    def test_valida_corpo(self):
        self.assertEqual(self.ca.patch(self.url, {}, format="json", **csrf(self.ca)).status_code, 400)
        self.assertEqual(self.ca.patch(self.url, {"is_active": "false"}, format="json", **csrf(self.ca)).status_code, 400)

    # ---- #10-2 + #10-3: excluir ----
    def test_excluir_bloqueia_e_preserva_projetos_e_documentos(self):
        cpo, _ = logar("po@x.com")
        r = self.ca.delete(self.url, **csrf(self.ca))
        self.assertEqual(r.status_code, 204)

        self.po.refresh_from_db()
        self.assertFalse(self.po.is_active)
        self.assertIsNotNone(self.po.excluido_em)

        self.assertEqual(cpo.get(BASE + "me/").status_code, 401)
        self.assertEqual(logar("po@x.com")[1].status_code, 401)

        # DoD #10-3: projetos e documentos intactos (registro do PO também continua no banco)
        self.assertTrue(UsuarioPO.objects.filter(pk=self.po.pk).exists())
        self.assertEqual(Projeto.objects.filter(usuario_po=self.po).count(), 1)
        self.assertEqual(Documento.objects.filter(projeto=self.proj).count(), 1)

        # fora da listagem por padrão, visível com incluir_excluidos
        ids = [u["id"] for u in self.ca.get(BASE + "admin/users/").json()]
        self.assertNotIn(self.po.id_po, ids)
        ids = [u["id"] for u in self.ca.get(BASE + "admin/users/?incluir_excluidos=true").json()]
        self.assertIn(self.po.id_po, ids)

        # login excluído se comporta como inexistente nas rotas de gestão
        self.assertEqual(self.ca.patch(self.url, {"is_active": True}, format="json", **csrf(self.ca)).status_code, 404)
        self.assertEqual(self.ca.delete(self.url, **csrf(self.ca)).status_code, 404)

    def test_refresh_tokens_vao_para_blacklist(self):
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
        logar("po@x.com")
        self.assertEqual(BlacklistedToken.objects.count(), 0)
        self.ca.patch(self.url, {"is_active": False}, format="json", **csrf(self.ca))
        self.assertEqual(BlacklistedToken.objects.count(), 1)

    def test_admin_nao_mexe_no_proprio_login(self):
        u = BASE + f"admin/users/{self.admin.id_po}/"
        self.assertEqual(self.ca.patch(u, {"is_active": False}, format="json", **csrf(self.ca)).status_code, 403)
        self.assertEqual(self.ca.delete(u, **csrf(self.ca)).status_code, 403)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_id_inexistente_404(self):
        self.assertEqual(self.ca.delete(BASE + "admin/users/9999/", **csrf(self.ca)).status_code, 404)

    def test_filtro_is_active_da_10_1_continua(self):
        self.ca.patch(self.url, {"is_active": False}, format="json", **csrf(self.ca))
        emails = [u["email"] for u in self.ca.get(BASE + "admin/users/?is_active=false").json()]
        self.assertEqual(emails, ["po@x.com"])