from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from projects.models import Projeto
from users.models import UsuarioPO
from users.views import LoginThrottle

LoginThrottle.rate = '1000/min'  # o throttle real (5/min) atrapalha testes que logam várias vezes

BASE = "/api/auth/"
URL = BASE + "admin/users/"
SENHA_OK = "Senha@Forte9"

VALIDADORES = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


def logar(email, senha="senha123"):
    c = APIClient(enforce_csrf_checks=True)
    r = c.post(BASE + "login/", {"email": email, "senha": senha}, format="json")
    return c, r


def csrf(c):
    return {"HTTP_X_CSRFTOKEN": c.cookies["csrftoken"].value}


def corpo(**extra):
    base = {"nome": "Maria PO", "email": "maria@x.com", "senha": SENHA_OK}
    base.update(extra)
    return base


class CadastroLoginTests(TestCase):
    """Task #10-6 — cadastro de PO pelo administrador."""

    def setUp(self):
        cache.clear()
        self.admin = UsuarioPO.objects.create_user("admin@x.com", "Admin", "senha123")
        self.admin.is_staff = True
        self.admin.save()
        self.ca, r = logar("admin@x.com")
        self.assertEqual(r.status_code, 200)

    def criar(self, **extra):
        return self.ca.post(URL, corpo(**extra), format="json", **csrf(self.ca))

    # ---- acesso ----
    def test_anonimo_nao_cadastra(self):
        c = APIClient(enforce_csrf_checks=True)
        self.assertIn(c.post(URL, corpo(), format="json").status_code, (401, 403))
        self.assertFalse(UsuarioPO.objects.filter(email="maria@x.com").exists())

    def test_nao_admin_recebe_403(self):
        UsuarioPO.objects.create_user("po@x.com", "PO", "senha123")
        c, r = logar("po@x.com")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(c.post(URL, corpo(), format="json", **csrf(c)).status_code, 403)
        self.assertFalse(UsuarioPO.objects.filter(email="maria@x.com").exists())

    def test_csrf_exigido(self):
        self.assertEqual(self.ca.post(URL, corpo(), format="json").status_code, 403)
        self.assertFalse(UsuarioPO.objects.filter(email="maria@x.com").exists())

    # ---- sucesso ----
    def test_cadastra_po_que_consegue_logar(self):
        r = self.criar()
        self.assertEqual(r.status_code, 201)
        dados = r.json()
        self.assertEqual(dados["nome"], "Maria PO")
        self.assertEqual(dados["email"], "maria@x.com")
        self.assertTrue(dados["is_active"])
        self.assertFalse(dados["is_admin"])
        self.assertIsNone(dados["excluido_em"])
        self.assertNotIn("senha", dados)
        self.assertNotIn("password", dados)

        novo = UsuarioPO.objects.get(email="maria@x.com")
        self.assertNotEqual(novo.password, SENHA_OK)  # guardada com hash
        self.assertTrue(novo.check_password(SENHA_OK))

        c, r = logar("maria@x.com", SENHA_OK)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], dados["id"])

    def test_novo_po_aparece_na_listagem(self):
        novo_id = self.criar().json()["id"]
        lista = self.ca.get(URL).json()
        self.assertIn(novo_id, [u["id"] for u in lista])

    def test_remove_espacos_e_padroniza_email_em_minusculas(self):
        r = self.criar(nome="  Maria PO  ", email="  Maria@X.com ")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["nome"], "Maria PO")
        self.assertEqual(r.json()["email"], "maria@x.com")

    def test_ignora_tentativa_de_criar_admin(self):
        r = self.criar(is_admin=True, is_staff=True, is_superuser=True, is_active=False)
        self.assertEqual(r.status_code, 201)
        novo = UsuarioPO.objects.get(email="maria@x.com")
        self.assertFalse(novo.is_staff)
        self.assertFalse(novo.is_superuser)
        self.assertTrue(novo.is_active)

    # ---- campos obrigatórios ----
    def test_campos_obrigatorios(self):
        r = self.ca.post(URL, {}, format="json", **csrf(self.ca))
        self.assertEqual(r.status_code, 400)
        campos = r.json()["campos"]
        self.assertEqual(set(campos), {"nome", "email", "senha"})
        self.assertEqual(UsuarioPO.objects.count(), 1)  # só o admin

    def test_campos_so_com_espacos_ou_tipo_errado_contam_como_vazios(self):
        r = self.criar(nome="   ", email=123, senha=["x"])
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()["campos"]), {"nome", "email", "senha"})

    def test_email_invalido(self):
        for ruim in ["maria", "maria@", "@x.com", "maria@x", "maria x@x.com"]:
            r = self.criar(email=ruim)
            self.assertEqual(r.status_code, 400, ruim)
            self.assertIn("email", r.json()["campos"], ruim)

    def test_limites_de_tamanho(self):
        r = self.criar(nome="a" * 101)
        self.assertEqual(r.status_code, 400)
        self.assertIn("nome", r.json()["campos"])
        r = self.criar(email="a" * 250 + "@x.com")
        self.assertEqual(r.status_code, 400)
        self.assertIn("email", r.json()["campos"])
        self.assertEqual(self.criar(nome="a" * 100).status_code, 201)

    def test_senha_curta(self):
        r = self.criar(senha="Ab@1")
        self.assertEqual(r.status_code, 400)
        self.assertIn("senha", r.json()["campos"])
        self.assertFalse(UsuarioPO.objects.filter(email="maria@x.com").exists())

    @override_settings(AUTH_PASSWORD_VALIDATORS=VALIDADORES)
    def test_senha_fraca_barrada_pelos_validadores_do_django(self):
        for fraca in ["12345678", "password", "maria@x.com"]:
            r = self.criar(senha=fraca)
            self.assertEqual(r.status_code, 400, fraca)
            self.assertIn("senha", r.json()["campos"], fraca)
        self.assertEqual(self.criar().status_code, 201)

    # ---- duplicidade ----
    def test_email_duplicado(self):
        self.assertEqual(self.criar().status_code, 201)
        r = self.criar(nome="Outra Maria")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["campos"]["email"], ["Já existe um login com este e-mail."])
        self.assertEqual(UsuarioPO.objects.filter(email__iexact="maria@x.com").count(), 1)

    def test_email_duplicado_ignora_maiusculas(self):
        self.assertEqual(self.criar().status_code, 201)
        r = self.criar(email="MARIA@X.COM")
        self.assertEqual(r.status_code, 400)
        self.assertIn("email", r.json()["campos"])

    def test_email_de_login_antigo_com_maiusculas_tambem_conta_como_duplicado(self):
        UsuarioPO.objects.create_user("Joao@x.com", "Joao", "senha123")  # criado fora da tela
        r = self.criar(email="joao@x.com")
        self.assertEqual(r.status_code, 400)
        self.assertIn("email", r.json()["campos"])

    def test_nao_cadastra_email_de_login_desativado(self):
        self.criar()
        alvo = UsuarioPO.objects.get(email="maria@x.com")
        self.ca.patch(URL + f"{alvo.id_po}/", {"is_active": False}, format="json", **csrf(self.ca))
        r = self.criar(nome="Outra")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["campos"]["email"], ["Já existe um login com este e-mail."])

    # ---- exclusão lógica x cadastro ----
    def test_excluir_nao_libera_email_nem_reaproveita_id(self):
        r = self.criar()
        id_excluido = r.json()["id"]
        po = UsuarioPO.objects.get(pk=id_excluido)
        proj = Projeto.objects.create(usuario_po=po, titulo="P", descricao="d")

        self.assertEqual(self.ca.delete(URL + f"{id_excluido}/", **csrf(self.ca)).status_code, 204)

        # o e-mail continua ocupado pelo registro excluído (que segue no banco)
        r2 = self.criar(nome="Maria de novo")
        self.assertEqual(r2.status_code, 400)
        self.assertEqual(
            r2.json()["campos"]["email"],
            ["Este e-mail pertence a um login excluído e não pode ser reutilizado."],
        )
        self.assertTrue(UsuarioPO.objects.filter(pk=id_excluido, excluido_em__isnull=False).exists())

        # um cadastro novo, com outro e-mail, recebe id novo — nunca o do excluído
        r3 = self.criar(nome="Joana", email="joana@x.com")
        self.assertEqual(r3.status_code, 201)
        self.assertGreater(r3.json()["id"], id_excluido)
        self.assertNotEqual(r3.json()["id"], id_excluido)

        # e os projetos do excluído seguem ligados a ele
        proj.refresh_from_db()
        self.assertEqual(proj.usuario_po_id, id_excluido)

    def test_cadastro_com_erro_nao_cria_nada(self):
        antes = UsuarioPO.objects.count()
        self.criar(senha="curta")
        self.criar(email="invalido")
        self.assertEqual(UsuarioPO.objects.count(), antes)

    def test_listagem_e_filtros_da_10_1_continuam_funcionando(self):
        self.criar()
        self.assertEqual(len(self.ca.get(URL).json()), 2)
        self.assertEqual(len(self.ca.get(URL + "?is_active=true").json()), 2)
        self.assertEqual(len(self.ca.get(URL + "?is_active=false").json()), 0)