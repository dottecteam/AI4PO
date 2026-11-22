from django.test import TestCase
from rest_framework.test import APIClient

from users.models import Competencia, Funcionario, UsuarioPO

URL = "/api/competencias/"


class GerenciamentoCompetenciasTests(TestCase):
    """Tela de gerenciamento de competências: cadastrar, renomear, excluir e contar profissionais."""

    def setUp(self):
        self.po = UsuarioPO.objects.create_user("po@x.com", "PO", "senha123")
        self.admin = UsuarioPO.objects.create_user("admin@x.com", "Admin", "senha123")
        self.admin.is_staff = True
        self.admin.save()
        self.py = Competencia.objects.create(nome="Python")
        self.dj = Competencia.objects.create(nome="Django")
        ana = Funcionario.objects.create(nome="Ana", email="ana@x.com")
        ana.competencias.set([self.py])

    def cliente(self, usuario):
        c = APIClient()
        c.force_authenticate(usuario)
        return c

    def test_lista_com_totais(self):
        dados = self.cliente(self.po).get(URL + "?com_totais=1").json()
        self.assertEqual(
            [(c["nome"], c["total_profissionais"]) for c in dados], [("Django", 0), ("Python", 1)]
        )
        # sem o parâmetro, o formato antigo continua igual
        self.assertEqual(set(self.cliente(self.po).get(URL).json()[0]), {"id", "nome"})

    def test_cadastra_normalizando_espacos_e_barra_duplicada(self):
        c = self.cliente(self.po)
        r = c.post(URL, {"nome": "  Machine   Learning "}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["nome"], "Machine Learning")
        r = c.post(URL, {"nome": "python"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("nome", r.json()["campos"])
        self.assertEqual(c.post(URL, {"nome": " "}, format="json").status_code, 400)

    def test_renomeia_sem_colidir(self):
        c = self.cliente(self.po)
        r = c.patch(f"{URL}{self.dj.pk}/", {"nome": "Django REST"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["nome"], "Django REST")
        self.assertEqual(c.patch(f"{URL}{self.dj.pk}/", {"nome": "PYTHON"}, format="json").status_code, 400)
        # renomear para o próprio nome (mudando maiúsculas) é permitido
        self.assertEqual(c.patch(f"{URL}{self.py.pk}/", {"nome": "PYTHON"}, format="json").status_code, 200)

    def test_somente_admin_exclui(self):
        self.assertEqual(self.cliente(self.po).delete(f"{URL}{self.py.pk}/").status_code, 403)
        self.assertEqual(self.cliente(self.admin).delete(f"{URL}{self.py.pk}/").status_code, 204)
        self.assertFalse(Competencia.objects.filter(pk=self.py.pk).exists())
        self.assertEqual(Funcionario.objects.get(email="ana@x.com").competencias.count(), 0)
        self.assertEqual(self.cliente(self.admin).delete(f"{URL}999/").status_code, 404)

    def test_exige_login(self):
        self.assertIn(APIClient().post(URL, {"nome": "X"}, format="json").status_code, (401, 403))
