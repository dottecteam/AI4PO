from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from projects.models import Projeto
from users.models import UsuarioPO
from users.views import LoginThrottle

LoginThrottle.rate = '1000/min'  # o throttle real (5/min) atrapalha testes que logam várias vezes

BASE = "/api/auth/"
SENHA_NOVA = "Outra@Senha77"

VALIDADORES = [
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


def logar(email, senha="senha123"):
    c = APIClient(enforce_csrf_checks=True)
    r = c.post(BASE + "login/", {"email": email, "senha": senha}, format="json")
    return c, r


def csrf(c):
    return {"HTTP_X_CSRFTOKEN": c.cookies["csrftoken"].value}


class EdicaoLoginTests(TestCase):
    """Task #10-8 — o administrador edita nome, e-mail e senha de um PO."""

    def setUp(self):
        cache.clear()
        self.admin = UsuarioPO.objects.create_user("admin@x.com", "Admin", "senha123")
        self.admin.is_staff = True
        self.admin.save()
        self.po = UsuarioPO.objects.create_user("po@x.com", "PO Um", "senha123")
        self.outro = UsuarioPO.objects.create_user("outro@x.com", "PO Dois", "senha123")
        self.ca, r = logar("admin@x.com")
        self.assertEqual(r.status_code, 200)
        self.url = BASE + f"admin/users/{self.po.id_po}/"

    def editar(self, corpo, url=None):
        return self.ca.patch(url or self.url, corpo, format="json", **csrf(self.ca))

    # ---- acesso ----
    def test_anonimo_e_nao_admin_nao_editam(self):
        self.assertIn(APIClient().patch(self.url, {"nome": "X"}, format="json").status_code, (401, 403))
        c, _ = logar("outro@x.com")
        self.assertEqual(c.patch(self.url, {"nome": "X"}, format="json", **csrf(c)).status_code, 403)
        self.po.refresh_from_db()
        self.assertEqual(self.po.nome, "PO Um")

    def test_csrf_exigido(self):
        self.assertEqual(self.ca.patch(self.url, {"nome": "X"}, format="json").status_code, 403)

    # ---- edição ----
    def test_edita_nome_e_email(self):
        r = self.editar({"nome": "  Maria Nova  ", "email": " Maria.Nova@X.com "})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["nome"], "Maria Nova")
        self.assertEqual(r.json()["email"], "maria.nova@x.com")
        self.assertEqual(r.json()["id"], self.po.id_po)
        self.po.refresh_from_db()
        self.assertEqual((self.po.nome, self.po.email), ("Maria Nova", "maria.nova@x.com"))
        # entra com o e-mail novo e não entra mais com o antigo
        self.assertEqual(logar("maria.nova@x.com")[1].status_code, 200)
        self.assertEqual(logar("po@x.com")[1].status_code, 401)

    def test_edicao_parcial_so_mexe_no_que_veio(self):
        self.assertEqual(self.editar({"nome": "Só o nome"}).status_code, 200)
        self.po.refresh_from_db()
        self.assertEqual((self.po.nome, self.po.email), ("Só o nome", "po@x.com"))
        self.assertTrue(self.po.check_password("senha123"))
        self.assertTrue(self.po.is_active)

    def test_manter_o_proprio_email_nao_conta_como_duplicado(self):
        r = self.editar({"nome": "Novo Nome", "email": "PO@x.com"})
        self.assertEqual(r.status_code, 200)

    def test_nao_promove_a_admin_nem_mexe_em_campos_nao_editaveis(self):
        r = self.editar({"nome": "X", "is_staff": True, "is_superuser": True, "excluido_em": None, "id_po": 999})
        self.assertEqual(r.status_code, 200)
        self.po.refresh_from_db()
        self.assertFalse(self.po.is_staff)
        self.assertFalse(self.po.is_superuser)
        self.assertEqual(self.po.id_po, self.url and int(self.url.rstrip("/").split("/")[-1]))

    def test_edita_e_muda_estado_no_mesmo_pedido(self):
        r = self.editar({"nome": "Novo", "is_active": False})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["nome"], "Novo")
        self.assertFalse(r.json()["is_active"])

    # ---- senha ----
    def test_troca_senha_e_derruba_sessoes_abertas(self):
        cpo, _ = logar("po@x.com")
        self.assertEqual(cpo.get(BASE + "me/").status_code, 200)
        r = self.editar({"senha": SENHA_NOVA})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("senha", r.json())
        self.assertNotIn("password", r.json())
        self.po.refresh_from_db()
        self.assertNotEqual(self.po.password, SENHA_NOVA)  # guardada com hash
        self.assertTrue(self.po.check_password(SENHA_NOVA))
        self.assertTrue(BlacklistedToken.objects.filter(token__user=self.po).exists())
        self.assertEqual(logar("po@x.com", "senha123")[1].status_code, 401)
        self.assertEqual(logar("po@x.com", SENHA_NOVA)[1].status_code, 200)

    def test_sem_senha_no_corpo_a_senha_nao_muda_e_sessoes_continuam(self):
        cpo, _ = logar("po@x.com")
        self.assertEqual(self.editar({"nome": "Outro Nome"}).status_code, 200)
        self.assertEqual(cpo.get(BASE + "me/").status_code, 200)
        self.assertFalse(BlacklistedToken.objects.filter(token__user=self.po).exists())

    def test_senha_curta_ou_vazia(self):
        for ruim in ["Ab@1", ""]:
            r = self.editar({"senha": ruim})
            self.assertEqual(r.status_code, 400, repr(ruim))
            self.assertIn("senha", r.json()["campos"])
        self.po.refresh_from_db()
        self.assertTrue(self.po.check_password("senha123"))

    @override_settings(AUTH_PASSWORD_VALIDATORS=VALIDADORES)
    def test_senha_fraca_barrada_pelos_validadores_do_django(self):
        r = self.editar({"senha": "12345678"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("senha", r.json()["campos"])

    # ---- validações ----
    def test_nome_e_email_nao_podem_ficar_vazios(self):
        r = self.editar({"nome": "   ", "email": ""})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()["campos"]), {"nome", "email"})
        self.po.refresh_from_db()
        self.assertEqual((self.po.nome, self.po.email), ("PO Um", "po@x.com"))

    def test_email_invalido_e_limites(self):
        for corpo in [{"email": "maria@"}, {"email": "a" * 250 + "@x.com"}, {"nome": "a" * 101}]:
            r = self.editar(corpo)
            self.assertEqual(r.status_code, 400, corpo)
            self.assertIn(next(iter(corpo)), r.json()["campos"])

    def test_email_duplicado_de_outro_login(self):
        r = self.editar({"email": "OUTRO@x.com"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["campos"]["email"], ["Já existe um login com este e-mail."])
        self.po.refresh_from_db()
        self.assertEqual(self.po.email, "po@x.com")

    def test_email_de_login_excluido_continua_barrado(self):
        self.ca.delete(BASE + f"admin/users/{self.outro.id_po}/", **csrf(self.ca))
        r = self.editar({"email": "outro@x.com"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json()["campos"]["email"],
            ["Este e-mail pertence a um login excluído e não pode ser reutilizado."],
        )

    def test_erro_em_um_campo_nao_grava_nenhum(self):
        r = self.editar({"nome": "Nome Válido", "email": "invalido", "is_active": False})
        self.assertEqual(r.status_code, 400)
        self.po.refresh_from_db()
        self.assertEqual(self.po.nome, "PO Um")
        self.assertTrue(self.po.is_active)

    def test_corpo_vazio_ou_nao_objeto(self):
        self.assertEqual(self.editar({}).status_code, 400)
        r = self.ca.generic("PATCH", self.url, "[1, 2]", content_type="application/json", **csrf(self.ca))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.editar({"is_active": "false"}).status_code, 400)

    # ---- regras que já existiam ----
    def test_nao_edita_o_proprio_login_nem_login_excluido(self):
        self_url = BASE + f"admin/users/{self.admin.id_po}/"
        self.assertEqual(self.editar({"nome": "Eu"}, self_url).status_code, 403)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.nome, "Admin")

        self.ca.delete(self.url, **csrf(self.ca))
        self.assertEqual(self.editar({"nome": "Fantasma"}).status_code, 404)

    def test_projetos_continuam_ligados_ao_po_editado(self):
        proj = Projeto.objects.create(usuario_po=self.po, titulo="P", descricao="d")
        self.editar({"nome": "Renomeado", "email": "renomeado@x.com"})
        proj.refresh_from_db()
        self.assertEqual(proj.usuario_po_id, self.po.id_po)