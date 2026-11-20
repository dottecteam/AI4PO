from django.test import TestCase
from rest_framework.test import APIClient

from atividades.models import Atividade
from users.models import Funcionario, UsuarioPO

from .models import Participacao, Projeto


class AtualizacaoParticipacaoTests(TestCase):
    """Task #15-3 — atualização do registro de participação pelo PO ou administrador."""

    def setUp(self):
        self.dono = UsuarioPO.objects.create_user("dono@x.com", "PO Dono", "senha123")
        self.outro = UsuarioPO.objects.create_user("outro@x.com", "Outro PO", "senha123")
        self.admin = UsuarioPO.objects.create_user("admin@x.com", "Admin", "senha123")
        self.admin.is_staff = True
        self.admin.save()

        self.projeto = Projeto.objects.create(usuario_po=self.dono, titulo="Portal", descricao="d")
        self.projeto_outro = Projeto.objects.create(usuario_po=self.outro, titulo="App", descricao="d")
        self.ana = Funcionario.objects.create(nome="Ana", email="ana@x.com")
        self.participacao = Participacao.objects.create(
            funcionario=self.ana, projeto=self.projeto, papel="Dev"
        )
        self.url = f"/api/participacoes/{self.participacao.id}/"

    def cliente(self, usuario):
        c = APIClient()
        c.force_authenticate(usuario)
        return c

    def test_po_responsavel_atualiza_o_papel(self):
        r = self.cliente(self.dono).patch(self.url, {"papel": "Tech Lead"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.participacao.refresh_from_db()
        self.assertEqual(self.participacao.papel, "Tech Lead")
        self.assertTrue(Atividade.objects.filter(acao="participacao_editada").exists())

    def test_admin_atualiza_qualquer_registro(self):
        r = self.cliente(self.admin).patch(
            self.url, {"papel": "Arquiteta", "projeto": self.projeto_outro.id}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.participacao.refresh_from_db()
        self.assertEqual((self.participacao.papel, self.participacao.projeto_id), ("Arquiteta", self.projeto_outro.id))

    def test_outro_po_nao_altera_nem_exclui(self):
        c = self.cliente(self.outro)
        self.assertEqual(c.patch(self.url, {"papel": "Hacker"}, format="json").status_code, 403)
        self.assertEqual(c.delete(self.url).status_code, 403)
        self.participacao.refresh_from_db()
        self.assertEqual(self.participacao.papel, "Dev")
        # leitura continua liberada
        self.assertEqual(c.get(self.url).status_code, 200)

    def test_po_nao_move_registro_para_projeto_de_outro_po(self):
        r = self.cliente(self.dono).patch(self.url, {"projeto": self.projeto_outro.id}, format="json")
        self.assertEqual(r.status_code, 403)
        self.participacao.refresh_from_db()
        self.assertEqual(self.participacao.projeto_id, self.projeto.id)

    def test_po_so_registra_em_projeto_que_organiza(self):
        c = self.cliente(self.outro)
        dados = {"funcionario": self.ana.id, "projeto": self.projeto.id, "papel": "QA"}
        self.assertEqual(c.post("/api/participacoes/", dados, format="json").status_code, 403)
        dados["projeto"] = self.projeto_outro.id
        self.assertEqual(c.post("/api/participacoes/", dados, format="json").status_code, 201)

    def test_atualizacao_duplicada_e_alertada(self):
        Participacao.objects.create(funcionario=self.ana, projeto=self.projeto, papel="QA")
        r = self.cliente(self.dono).patch(self.url, {"papel": "qa"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_dono_exclui_registro(self):
        self.assertEqual(self.cliente(self.dono).delete(self.url).status_code, 204)
        self.assertFalse(Participacao.objects.filter(pk=self.participacao.pk).exists())

    def test_perfil_indica_o_que_o_usuario_pode_editar(self):
        dados = self.cliente(self.outro).get(f"/api/profissionais/{self.ana.id}/").json()
        self.assertFalse(dados["participacoes"][0]["pode_editar"])
        self.assertEqual([p["titulo"] for p in dados["projetos_gerenciaveis"]], ["App"])

        dados = self.cliente(self.admin).get(f"/api/profissionais/{self.ana.id}/").json()
        self.assertTrue(dados["participacoes"][0]["pode_editar"])
        self.assertEqual(len(dados["projetos_gerenciaveis"]), 2)
