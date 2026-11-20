from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from users.models import Competencia, Funcionario, UsuarioPO
from users.views import LoginThrottle

LoginThrottle.rate = '1000/min'  # o throttle real (5/min) atrapalha testes que logam várias vezes

BASE = "/api/auth/"
URL = "/api/profissionais/"
URL_COMP = "/api/competencias/"


def logar(email, senha="senha123"):
    c = APIClient(enforce_csrf_checks=True)
    r = c.post(BASE + "login/", {"email": email, "senha": senha}, format="json")
    return c, r


def csrf(c):
    return {"HTTP_X_CSRFTOKEN": c.cookies["csrftoken"].value}


class ProfissionaisCadastroTests(TestCase):
    """Task #14-3 — rotas de apoio da tela: competências, listagem e cadastro de profissionais."""

    def setUp(self):
        cache.clear()
        UsuarioPO.objects.create_user("po@x.com", "PO", "senha123")  # PO comum, não admin
        self.c, r = logar("po@x.com")
        self.assertEqual(r.status_code, 200)
        self.py = Competencia.objects.create(nome="Python")
        self.dj = Competencia.objects.create(nome="django")  # minúscula de propósito
        self.re = Competencia.objects.create(nome="React")

    def criar(self, **extra):
        corpo = {"nome": "Maria Souza", "email": "maria@x.com", "competencias": [self.py.pk, self.re.pk]}
        corpo.update(extra)
        return self.c.post(URL, corpo, format="json", **csrf(self.c))

    # ---- acesso ----
    def test_anonimo_nao_acessa_nenhuma_rota(self):
        anon = APIClient()
        self.assertIn(anon.get(URL_COMP).status_code, (401, 403))
        self.assertIn(anon.get(URL).status_code, (401, 403))
        self.assertIn(anon.post(URL, {}, format="json").status_code, (401, 403))

    def test_po_comum_acessa_e_cadastra_sem_ser_admin(self):
        self.assertEqual(self.c.get(URL_COMP).status_code, 200)
        self.assertEqual(self.c.get(URL).status_code, 200)
        self.assertEqual(self.criar().status_code, 201)

    def test_csrf_exigido_no_cadastro(self):
        r = self.c.post(URL, {"nome": "X", "email": "x@x.com", "competencias": [self.py.pk]}, format="json")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Funcionario.objects.count(), 0)

    # ---- competências ----
    def test_lista_competencias_em_ordem_alfabetica_sem_diferenciar_maiusculas(self):
        r = self.c.get(URL_COMP)
        self.assertEqual([c["nome"] for c in r.json()], ["django", "Python", "React"])
        self.assertEqual(set(r.json()[0]), {"id", "nome"})

    # ---- listagem ----
    def test_lista_profissionais_com_competencias_em_ordem_alfabetica(self):
        for nome, comps in [("bruno", [self.re, self.py]), ("Ana", [self.dj])]:
            f = Funcionario.objects.create(nome=nome, email=f"{nome.lower()}@x.com")
            f.competencias.set(comps)
        r = self.c.get(URL)
        self.assertEqual([p["nome"] for p in r.json()], ["Ana", "bruno"])
        self.assertEqual([c["nome"] for c in r.json()[1]["competencias"]], ["Python", "React"])
        self.assertEqual(set(r.json()[0]), {"id", "nome", "email", "competencias"})

    def test_lista_vazia(self):
        self.assertEqual(self.c.get(URL).json(), [])

    # ---- cadastro ----
    def test_cadastra_e_devolve_o_profissional(self):
        r = self.criar(nome="  Maria Souza  ", email=" Maria@X.com ")
        self.assertEqual(r.status_code, 201)
        dados = r.json()
        self.assertEqual(dados["nome"], "Maria Souza")
        self.assertEqual(dados["email"], "maria@x.com")
        self.assertEqual([c["nome"] for c in dados["competencias"]], ["Python", "React"])
        f = Funcionario.objects.get(pk=dados["id"])
        self.assertEqual(set(f.competencias.values_list("pk", flat=True)), {self.py.pk, self.re.pk})

    def test_profissional_cadastrado_aparece_na_listagem_e_na_busca(self):
        novo_id = self.criar().json()["id"]
        self.assertIn(novo_id, [p["id"] for p in self.c.get(URL).json()])
        busca = self.c.get("/api/profissionais/busca/", {"competencias": str(self.py.pk)}).json()
        self.assertEqual([p["id"] for p in busca["resultados"]], [novo_id])

    def test_aceita_ids_como_texto_e_ignora_repetidos(self):
        r = self.criar(competencias=[str(self.py.pk), self.py.pk, self.py.pk])
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(r.json()["competencias"]), 1)

    # ---- validações ----
    def test_campos_obrigatorios(self):
        r = self.c.post(URL, {}, format="json", **csrf(self.c))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()["campos"]), {"nome", "email", "competencias"})
        self.assertEqual(Funcionario.objects.count(), 0)

    def test_so_espacos_e_tipo_errado_contam_como_vazios(self):
        r = self.criar(nome="   ", email=123, competencias="1,2")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()["campos"]), {"nome", "email", "competencias"})

    def test_exige_ao_menos_uma_competencia(self):
        r = self.criar(competencias=[])
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["campos"]["competencias"], ["Selecione ao menos uma competência."])

    def test_competencia_invalida_ou_inexistente(self):
        for ruim in [["abc"], [True], [1.5], [-1], [0], [None], [9999999999]]:
            r = self.criar(competencias=ruim)
            self.assertEqual(r.status_code, 400, ruim)
            self.assertIn("competencias", r.json()["campos"], ruim)
        r = self.criar(competencias=[self.py.pk, 99999])
        self.assertEqual(r.status_code, 400)
        self.assertIn("99999", r.json()["campos"]["competencias"][0])
        self.assertEqual(Funcionario.objects.count(), 0)

    def test_email_invalido_e_limites(self):
        for corpo in [{"email": "maria@"}, {"email": "a" * 250 + "@x.com"}, {"nome": "a" * 256}]:
            r = self.criar(**corpo)
            self.assertEqual(r.status_code, 400, corpo)
            self.assertIn(next(iter(corpo)), r.json()["campos"])
        self.assertEqual(self.criar(nome="a" * 255).status_code, 201)

    def test_email_duplicado_sem_diferenciar_maiusculas(self):
        self.assertEqual(self.criar().status_code, 201)
        for repetido in ["maria@x.com", "MARIA@X.COM"]:
            r = self.criar(nome="Outra", email=repetido)
            self.assertEqual(r.status_code, 400, repetido)
            self.assertEqual(r.json()["campos"]["email"], ["Já existe um profissional com este e-mail."])
        self.assertEqual(Funcionario.objects.count(), 1)

    def test_email_de_funcionario_criado_fora_da_tela_com_maiusculas_tambem_conta(self):
        Funcionario.objects.create(nome="Joao", email="Joao@x.com")
        r = self.criar(email="joao@x.com")
        self.assertEqual(r.status_code, 400)
        self.assertIn("email", r.json()["campos"])

    def test_erro_nao_cria_nada(self):
        self.criar(email="invalido")
        self.criar(competencias=[])
        self.assertEqual(Funcionario.objects.count(), 0)

    def test_corpo_que_nao_e_objeto(self):
        r = self.c.generic("POST", URL, "[1, 2]", content_type="application/json", **csrf(self.c))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json()["campos"]), {"nome", "email", "competencias"})