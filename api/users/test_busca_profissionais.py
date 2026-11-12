from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from users.models import Competencia, Funcionario, UsuarioPO
from users.views import LoginThrottle

LoginThrottle.rate = '1000/min'  # o throttle real (5/min) atrapalha testes que logam várias vezes

BASE = "/api/auth/"
URL = "/api/profissionais/busca/"


def logar(email, senha="senha123"):
    c = APIClient(enforce_csrf_checks=True)
    r = c.post(BASE + "login/", {"email": email, "senha": senha}, format="json")
    return c, r


def nomes(resposta):
    return [p["nome"] for p in resposta.json()["resultados"]]


class BuscaProfissionaisTests(TestCase):
    """Task #14-2 — busca de profissionais por competência, ordenados por afinidade."""

    def setUp(self):
        cache.clear()
        self.po = UsuarioPO.objects.create_user("po@x.com", "PO", "senha123")
        self.c, r = logar("po@x.com")
        self.assertEqual(r.status_code, 200)

        self.py = Competencia.objects.create(nome="Python")
        self.dj = Competencia.objects.create(nome="Django")
        self.re = Competencia.objects.create(nome="React")
        self.dk = Competencia.objects.create(nome="Docker")

        def func(nome, *competencias):
            f = Funcionario.objects.create(nome=nome, email=f"{nome.lower()}@x.com")
            f.competencias.set(competencias)
            return f

        # Busca padrão: Python + Django + React
        func("Ana", self.py, self.dj, self.re)          # 3 de 3, total 3
        func("Fabio", self.py, self.dj, self.re)        # 3 de 3, total 3 (empata com Ana)
        func("bia", self.py, self.dj, self.re)          # 3 de 3, total 3 (nome em minúsculas)
        func("Bruno", self.py, self.dj, self.re, self.dk)  # 3 de 3, total 4 (menos foco)
        func("Carla", self.py, self.dj)                 # 2 de 3
        func("Diego", self.py)                          # 1 de 3
        func("Eva", self.dk)                            # nenhuma das buscadas
        func("Gui")                                     # sem nenhuma competência

        self.ids = f"{self.py.pk},{self.dj.pk},{self.re.pk}"

    def buscar(self, **params):
        return self.c.get(URL, params)

    # ---- acesso ----
    def test_anonimo_nao_acessa(self):
        r = APIClient().get(URL, {"competencias": self.ids})
        self.assertIn(r.status_code, (401, 403))

    def test_qualquer_po_logado_acessa_nao_so_admin(self):
        self.assertFalse(self.po.is_staff)
        self.assertEqual(self.buscar(competencias=self.ids).status_code, 200)

    def test_login_desativado_perde_o_acesso(self):
        self.po.is_active = False
        self.po.save()
        self.assertEqual(self.buscar(competencias=self.ids).status_code, 401)

    def test_so_aceita_get(self):
        token = self.c.cookies["csrftoken"].value
        r = self.c.post(URL, {}, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code, 405)

    # ---- ordenação por afinidade ----
    def test_ordena_por_afinidade_depois_foco_depois_nome(self):
        r = self.buscar(competencias=self.ids)
        self.assertEqual(r.status_code, 200)
        # 3 de 3 (foco 100%): Ana, bia, Fabio (nome sem diferenciar maiúsculas)
        # 3 de 3 (foco 75%): Bruno | 2 de 3: Carla | 1 de 3: Diego
        self.assertEqual(nomes(r), ["Ana", "bia", "Fabio", "Bruno", "Carla", "Diego"])

    def test_nao_lista_quem_nao_tem_nenhuma_das_competencias_buscadas(self):
        r = self.buscar(competencias=self.ids)
        self.assertNotIn("Eva", nomes(r))
        self.assertNotIn("Gui", nomes(r))
        self.assertEqual(r.json()["total"], 6)
        self.assertEqual(r.json()["total"], len(r.json()["resultados"]))

    def test_competencia_que_ninguem_tem_devolve_lista_vazia(self):
        rust = Competencia.objects.create(nome="Rust")
        r = self.buscar(competencias=str(rust.pk))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["total"], 0)
        self.assertEqual(r.json()["resultados"], [])
        self.assertEqual(r.json()["criterios"]["competencias_buscadas"], [{"id": rust.pk, "nome": "Rust"}])

    def test_busca_por_uma_competencia_so(self):
        r = self.buscar(competencias=str(self.dk.pk))
        # ambos têm 100% de afinidade; Eva tem foco 100% e Bruno 25%
        self.assertEqual(nomes(r), ["Eva", "Bruno"])

    # ---- critérios na resposta ----
    def test_resposta_traz_os_criterios_usados(self):
        criterios = self.buscar(competencias=self.ids).json()["criterios"]
        self.assertEqual([c["nome"] for c in criterios["competencias_buscadas"]], ["Django", "Python", "React"])
        self.assertIn("competências buscadas", criterios["afinidade"])
        self.assertEqual(len(criterios["ordenacao"]), 3)

    def test_cada_profissional_traz_afinidade_correspondentes_faltantes_e_foco(self):
        por_nome = {p["nome"]: p for p in self.buscar(competencias=self.ids).json()["resultados"]}

        ana = por_nome["Ana"]
        self.assertEqual(ana["afinidade"], 100.0)
        self.assertEqual(ana["foco"], 100.0)
        self.assertEqual(ana["total_competencias"], 3)
        self.assertEqual(ana["competencias_faltantes"], [])
        self.assertEqual(ana["email"], "ana@x.com")

        bruno = por_nome["Bruno"]
        self.assertEqual(bruno["afinidade"], 100.0)
        self.assertEqual(bruno["foco"], 75.0)
        self.assertEqual(bruno["total_competencias"], 4)
        self.assertEqual([c["nome"] for c in bruno["competencias_correspondentes"]], ["Django", "Python", "React"])
        # o Docker que ele tem não entra: não foi buscado
        self.assertNotIn("Docker", [c["nome"] for c in bruno["competencias_correspondentes"]])

        carla = por_nome["Carla"]
        self.assertEqual(carla["afinidade"], 66.7)
        self.assertEqual([c["nome"] for c in carla["competencias_correspondentes"]], ["Django", "Python"])
        self.assertEqual(carla["competencias_faltantes"], [{"id": self.re.pk, "nome": "React"}])

        diego = por_nome["Diego"]
        self.assertEqual(diego["afinidade"], 33.3)
        self.assertEqual(diego["foco"], 100.0)
        self.assertEqual([c["nome"] for c in diego["competencias_faltantes"]], ["Django", "React"])

    def test_total_de_competencias_conta_todas_e_nao_so_as_buscadas(self):
        # regressão: filtrar antes de agregar faria o total de Bruno virar 3 em vez de 4
        bruno = next(p for p in self.buscar(competencias=self.ids).json()["resultados"] if p["nome"] == "Bruno")
        self.assertEqual(bruno["total_competencias"], 4)

    # ---- formas de informar a busca ----
    def test_busca_por_nome_sem_diferenciar_maiusculas(self):
        r = self.buscar(nomes="python,DJANGO")
        self.assertEqual(r.status_code, 200)
        self.assertEqual([c["nome"] for c in r.json()["criterios"]["competencias_buscadas"]], ["Django", "Python"])
        self.assertEqual(nomes(r), ["Carla", "Ana", "bia", "Fabio", "Bruno", "Diego"])

    def test_ids_e_nomes_se_somam(self):
        r = self.buscar(competencias=str(self.py.pk), nomes="Django")
        self.assertEqual([c["nome"] for c in r.json()["criterios"]["competencias_buscadas"]], ["Django", "Python"])

    def test_parametro_repetido_funciona_como_lista(self):
        r = self.c.get(f"{URL}?competencias={self.py.pk}&competencias={self.dj.pk}&competencias={self.re.pk}")
        self.assertEqual(nomes(r), ["Ana", "bia", "Fabio", "Bruno", "Carla", "Diego"])

    def test_espacos_e_virgulas_sobrando_sao_ignorados(self):
        r = self.buscar(competencias=f" {self.py.pk} ,, {self.dj.pk},")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["criterios"]["competencias_buscadas"]), 2)

    def test_repetir_a_mesma_competencia_nao_infla_a_afinidade(self):
        r = self.buscar(competencias=f"{self.py.pk},{self.py.pk}", nomes="PYTHON,python")
        self.assertEqual(len(r.json()["criterios"]["competencias_buscadas"]), 1)
        self.assertTrue(all(p["afinidade"] == 100.0 for p in r.json()["resultados"]))

    # ---- validações ----
    def test_exige_ao_menos_uma_competencia(self):
        for params in [{}, {"competencias": ""}, {"competencias": " , "}, {"nomes": ""}]:
            r = self.buscar(**params)
            self.assertEqual(r.status_code, 400, params)
            self.assertIn("competencias", r.json()["campos"])

    def test_ids_invalidos(self):
        for ruim in ["abc", "1.5", "-1", "9999999999", f"{self.py.pk},x"]:
            r = self.buscar(competencias=ruim)
            self.assertEqual(r.status_code, 400, ruim)
            self.assertIn("inválidos", r.json()["campos"]["competencias"][0])

    def test_id_inexistente_avisa_em_vez_de_ignorar(self):
        r = self.buscar(competencias=f"{self.py.pk},99999")
        self.assertEqual(r.status_code, 400)
        self.assertIn("99999", r.json()["campos"]["competencias"][0])

    def test_nome_inexistente_avisa_em_vez_de_ignorar(self):
        r = self.buscar(nomes="Python,Cobol")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Cobol", r.json()["campos"]["nomes"][0])

    def test_limite_de_competencias_por_busca(self):
        r = self.buscar(competencias=",".join(str(i) for i in range(1, 32)))
        self.assertEqual(r.status_code, 400)
        self.assertIn("no máximo 30", r.json()["campos"]["competencias"][0])

    # ---- consultas ----
    def test_numero_de_consultas_nao_cresce_com_a_quantidade_de_profissionais(self):
        with CaptureQueriesContext(connection) as antes:
            self.assertEqual(self.buscar(competencias=self.ids).status_code, 200)

        for i in range(15):
            f = Funcionario.objects.create(nome=f"Extra{i}", email=f"extra{i}@x.com")
            f.competencias.set([self.py, self.dk])

        with CaptureQueriesContext(connection) as depois:
            r = self.buscar(competencias=self.ids)
        self.assertEqual(r.json()["total"], 21)
        self.assertEqual(len(depois), len(antes))
        self.assertLessEqual(len(depois), 6)