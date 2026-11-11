from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from backlog.models import Cenario, Epico, Feature, PBI
from projects.models import Projeto


class EscopoBacklogEntrePOsTests(TestCase):
    """Cada nivel da hierarquia so e visivel pelo PO dono do projeto.

    Estes testes falham de proposito se `users.permissions.escopo` for removido
    de backlog/views.py: antes do escopo, um PO listava e editava Epico, Feature,
    PBI e Cenario dos projetos alheios.
    """

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.dono = User.objects.create_user(
            email="dono-backlog@test.com", nome="Dono do Backlog")
        cls.intruso = User.objects.create_user(
            email="intruso-backlog@test.com", nome="Intruso")

        cls.projeto = Projeto.objects.create(
            usuario_po=cls.dono, titulo="PayCore", descricao="pagamentos")
        cls.epico = Epico.objects.create(
            projeto=cls.projeto, titulo="Digitalizar solicitações",
            descricao="d", objetivo="o", resultado="r")
        cls.feature = Feature.objects.create(
            epico=cls.epico, titulo="Consultar andamento",
            descricao="d", objetivo="o")
        cls.pbi = PBI.objects.create(
            feature=cls.feature, titulo="Listar solicitações",
            userstory_como="cliente", userstory_quero="ver as solicitações",
            userstory_paraque="acompanhar o andamento",
            criterio_de_aceitacao="lista vazia quando não há solicitações")
        cls.cenario = Cenario.objects.create(
            pbi=cls.pbi, dado="o cliente está autenticado",
            quando="ele abre a lista", entao="as solicitações aparecem")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.intruso)

    def test_nenhum_nivel_aparece_na_lista_para_outro_po(self):
        rotinas = [
            ("epico-list-create", {"idProjeto": self.projeto.pk}),
            ("feature-list-create", {"idEpico": self.epico.pk}),
            ("pbi-list-create", {"idFeature": self.feature.pk}),
            ("cenario-list-create", {}),
        ]
        for nome, parametros in rotinas:
            with self.subTest(rotina=nome):
                resposta = self.client.get(reverse(nome), parametros)
                self.assertEqual(resposta.status_code, 200)
                # Sem paginacao configurada, a lista vem como array puro.
                self.assertEqual(resposta.json(), [])

    def test_detalhe_de_cada_nivel_da_404_para_intruso(self):
        casos = [
            ("epico-detail", self.epico.pk),
            ("feature-detail", self.feature.pk),
            ("pbi-detail", self.pbi.pk),
            ("cenario-detail", self.cenario.pk),
        ]
        for nome, pk in casos:
            with self.subTest(rotina=nome):
                resposta = self.client.get(reverse(nome, args=[pk]))
                self.assertEqual(resposta.status_code, 404)

    def test_intruso_nao_edita_nem_apaga_nivel_alheio(self):
        for nome, pk in [("epico-detail", self.epico.pk),
                         ("feature-detail", self.feature.pk),
                         ("pbi-detail", self.pbi.pk),
                         ("cenario-detail", self.cenario.pk)]:
            with self.subTest(rotina=nome):
                resposta = self.client.patch(
                    reverse(nome, args=[pk]), {"titulo": "sequestrado"},
                    format="json")
                self.assertEqual(resposta.status_code, 404)
                self.assertEqual(self.client.delete(
                    reverse(nome, args=[pk])).status_code, 404)

        # Nada mudou no banco: o 404 nao pode ter escrito nada.
        self.epico.refresh_from_db()
        self.assertEqual(self.epico.titulo, "Digitalizar solicitações")
        self.assertTrue(Cenario.objects.filter(pk=self.cenario.pk).exists())

    def test_dono_continua_enxergando_a_propria_arvore(self):
        """O escopo nao pode quebrar o caminho feliz de quem e o dono."""
        self.client.force_authenticate(self.dono)
        for nome, pk in [("epico-detail", self.epico.pk),
                         ("feature-detail", self.feature.pk),
                         ("pbi-detail", self.pbi.pk),
                         ("cenario-detail", self.cenario.pk)]:
            with self.subTest(rotina=nome):
                resposta = self.client.get(reverse(nome, args=[pk]))
                self.assertEqual(resposta.status_code, 200)

        self.assertEqual(
            len(self.client.get(
                reverse("epico-list-create"),
                {"idProjeto": self.projeto.pk}).json()), 1)
