from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from .models import Conversa, Mensagem


class ExportarPDFTests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(nome="Usuario 1", email="a@a.com", password="123456")
        self.outro = User.objects.create_user(nome="Usuario 2", email="b@b.com", password="123456")

        self.conversa = Conversa.objects.create(usuario=self.user, titulo="Teste")
        Mensagem.objects.create(conversa=self.conversa, role="user", conteudo="Olá, ação")
        Mensagem.objects.create(conversa=self.conversa, role="assistant", conteudo="Resposta")

        self.client = APIClient()
        self.url = f"/api/conversas/{self.conversa.pk}/exportar-pdf/"

    def test_exporta_pdf(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "application/pdf")
        self.assertTrue(res.content.startswith(b"%PDF"))

    def test_exige_login(self):
        res = self.client.get(self.url)
        self.assertIn(res.status_code, (401, 403))

    def test_nao_exporta_conversa_de_outro_usuario(self):
        self.client.force_authenticate(self.outro)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 404)