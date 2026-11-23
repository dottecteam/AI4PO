from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from projects.models import Participacao, Projeto
from users.models import Competencia, Funcionario, UsuarioPO

URL = "/api/dashboard/graficos/"


class GraficosDashboardTests(TestCase):
    def setUp(self):
        self.po = UsuarioPO.objects.create_user("po@x.com", "PO", "senha123")
        outro = UsuarioPO.objects.create_user("outro@x.com", "Outro", "senha123")
        self.p1 = Projeto.objects.create(usuario_po=self.po, titulo="A", descricao="d", status="Ativo")
        self.p2 = Projeto.objects.create(usuario_po=self.po, titulo="B", descricao="d")
        Projeto.objects.filter(pk=self.p2.pk).update(criado_em=timezone.now() - timedelta(days=40))
        Projeto.objects.create(usuario_po=outro, titulo="C", descricao="d")  # de outro PO

        py = Competencia.objects.create(nome="Python")
        Competencia.objects.create(nome="Figma")  # ninguém tem
        ana = Funcionario.objects.create(nome="Ana", email="ana@x.com")
        ana.competencias.set([py])
        Funcionario.objects.create(nome="Bia", email="bia@x.com")  # sem projeto
        Participacao.objects.create(funcionario=ana, projeto=self.p1, papel="Dev")
        Participacao.objects.create(funcionario=ana, projeto=self.p1, papel="QA")  # mesmo projeto
        Participacao.objects.create(funcionario=ana, projeto=self.p2, papel="Dev")

        self.client = APIClient()
        self.client.force_authenticate(self.po)

    def test_series_do_dashboard(self):
        dados = self.client.get(URL).json()

        meses = dados["projetos_por_mes"]
        self.assertEqual(len(meses), 6)
        self.assertEqual(meses[-1]["total"], 1)  # só os projetos do próprio PO
        self.assertEqual(sum(m["total"] for m in meses), 2)

        status = {s["status"]: s["total"] for s in dados["projetos_por_status"]}
        self.assertEqual(status, {"Rascunho": 1, "Inativo": 0, "Ativo": 1})

        # Ana: 2 projetos distintos; Bia: 0 -> média 1,0
        self.assertEqual(
            dados["equipe"],
            {"profissionais": 2, "media_projetos_por_profissional": 1.0, "sem_projeto": 1, "competencias": 2},
        )
        self.assertEqual(dados["top_competencias"], [{"id": dados["top_competencias"][0]["id"], "nome": "Python", "total": 1}])
        self.assertEqual([(p["nome"], p["total"]) for p in dados["top_profissionais"]], [("Ana", 2)])

    def test_exige_login(self):
        self.assertEqual(APIClient().get(URL).status_code, 401)
