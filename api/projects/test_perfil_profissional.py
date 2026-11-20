from django.test import TestCase
from rest_framework.test import APIClient

from users.models import Competencia, Funcionario, UsuarioPO

from .models import Participacao, Projeto


class PerfilProfissionalTests(TestCase):
    """Task #15-2 — perfil do profissional com projetos, papéis e competências."""

    def setUp(self):
        self.po = UsuarioPO.objects.create_user("po@x.com", "Maria PO", "senha123")
        self.client = APIClient()
        self.client.force_authenticate(self.po)

        self.django = Competencia.objects.create(nome="Django")
        self.react = Competencia.objects.create(nome="React")
        self.ana = Funcionario.objects.create(nome="Ana", email="ana@x.com")
        self.ana.competencias.set([self.react, self.django])
        self.bruno = Funcionario.objects.create(nome="Bruno", email="po@x.com")

        self.p1 = Projeto.objects.create(usuario_po=self.po, titulo="Portal", descricao="d")
        self.p2 = Projeto.objects.create(usuario_po=self.po, titulo="App", descricao="d")
        Participacao.objects.create(funcionario=self.ana, projeto=self.p1, papel="Dev")
        Participacao.objects.create(funcionario=self.ana, projeto=self.p1, papel="Tech Lead")
        Participacao.objects.create(funcionario=self.ana, projeto=self.p2, papel="Dev")

    def test_perfil_exibe_projetos_papeis_e_competencias(self):
        r = self.client.get(f"/api/profissionais/{self.ana.id}/")
        self.assertEqual(r.status_code, 200)
        dados = r.json()
        self.assertEqual(dados["nome"], "Ana")
        self.assertEqual([c["nome"] for c in dados["competencias"]], ["Django", "React"])
        self.assertEqual(len(dados["participacoes"]), 3)
        self.assertEqual(
            {(p["projeto"]["titulo"], p["papel"]) for p in dados["participacoes"]},
            {("Portal", "Dev"), ("Portal", "Tech Lead"), ("App", "Dev")},
        )

    def test_lista_com_busca_por_competencia(self):
        r = self.client.get("/api/profissionais/?busca=djan")
        self.assertEqual(r.status_code, 200)
        dados = r.json()
        self.assertEqual([p["nome"] for p in dados], ["Ana"])
        self.assertEqual(dados[0]["total_projetos"], 2)

    def test_meu_perfil_vinculado_pelo_email(self):
        r = self.client.get("/api/profissionais/me/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], self.bruno.id)

        self.bruno.delete()
        self.assertEqual(self.client.get("/api/profissionais/me/").status_code, 204)

    def test_perfil_inexistente_e_exige_login(self):
        self.assertEqual(self.client.get("/api/profissionais/9999/").status_code, 404)
        self.assertEqual(APIClient().get(f"/api/profissionais/{self.ana.id}/").status_code, 401)
