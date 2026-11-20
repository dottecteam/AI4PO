from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from projects.models import Projeto
from users.models import Competencia, Funcionario, UsuarioPO

from .models import MensagemChat

CHAT = "/api/chat/"


def chamada(ferramenta, **args):
    return {"content": "", "tool_calls": [{"function": {"name": ferramenta, "arguments": args}}]}


@patch("ai.views.gerar_titulo", return_value=None)
@patch("ai.views.classificar_intencao", return_value=("acao", "pbi"))
class AcoesChatTests(TestCase):
    """Cadastros pelo chat: validação no servidor, pergunta quando falta dado e confirmação explícita."""

    def setUp(self):
        self.po = UsuarioPO.objects.create_user("po@x.com", "PO", "senha123")
        self.admin = UsuarioPO.objects.create_user("admin@x.com", "Admin", "senha123")
        self.admin.is_staff = True
        self.admin.save()
        Competencia.objects.create(nome="Python")
        self.c = self.cliente(self.po)

    def cliente(self, usuario):
        c = APIClient()
        c.force_authenticate(usuario)
        return c

    def enviar(self, texto, conversa_id=None, cliente=None):
        corpo = {"message": texto}
        if conversa_id:
            corpo["conversa_id"] = conversa_id
        return (cliente or self.c).post(CHAT, corpo, format="json").json()

    def decidir(self, acao, decisao, cliente=None):
        return (cliente or self.c).post(f"/api/chat/acoes/{acao['mensagem_id']}/{decisao}/")

    @patch("ai.views._chamar_ollama")
    def test_projeto_so_e_criado_apos_confirmar(self, ollama, *_):
        ollama.return_value = chamada("cadastrar_projeto", titulo="Portal", descricao="Portal interno")
        dados = self.enviar("Cadastre o projeto Portal, um portal interno")
        acao = dados["acao"]
        self.assertEqual((acao["tipo"], acao["estado"]), ("projeto", "pendente"))
        self.assertEqual(acao["dados"]["status"], "Rascunho")
        self.assertFalse(Projeto.objects.exists())

        r = self.decidir(acao, "confirmar")
        self.assertEqual(r.status_code, 200)
        projeto = Projeto.objects.get()
        self.assertEqual((projeto.titulo, projeto.usuario_po), ("Portal", self.po))
        self.assertEqual(r.json()["acao"]["resultado"]["link"], f"/projetos/{projeto.id}")
        # não confirma duas vezes
        self.assertEqual(self.decidir(acao, "confirmar").status_code, 409)

    @patch("ai.views._chamar_ollama")
    def test_dado_faltando_vira_pergunta_e_resposta_continua_o_fluxo(self, ollama, classificar, _):
        ollama.return_value = chamada("cadastrar_projeto", titulo="Portal", descricao="")
        dados = self.enviar("Cadastre o projeto Portal")
        self.assertIsNone(dados["acao"])
        self.assertIn("descrição", dados["pergunta"]["texto"])

        # a resposta do usuário volta direto para o fluxo de cadastro, sem passar pelo roteador
        classificar.reset_mock()
        ollama.return_value = chamada("cadastrar_projeto", titulo="Portal", descricao="Portal interno")
        dados = self.enviar("É um portal interno de RH", conversa_id=dados["conversa_id"])
        classificar.assert_not_called()
        self.assertEqual(dados["acao"]["tipo"], "projeto")

    @patch("ai.views._chamar_ollama")
    def test_pergunta_do_modelo_com_opcoes(self, ollama, *_):
        ollama.return_value = chamada("perguntar_ao_usuario", pergunta="O que cadastrar?", opcoes=["Projeto", "Profissional"])
        dados = self.enviar("/cadastrar")
        self.assertEqual(dados["pergunta"], {"texto": "O que cadastrar?", "opcoes": ["Projeto", "Profissional"]})

    @patch("ai.views._chamar_ollama")
    def test_profissional_cria_competencias_novas_ao_confirmar(self, ollama, *_):
        ollama.return_value = chamada(
            "cadastrar_profissional", nome="Maria", email="Maria@X.com", competencias=["python", "Figma"]
        )
        acao = self.enviar("Adicione a Maria")["acao"]
        self.assertEqual(acao["dados"]["competencias"], ["Python"])
        self.assertEqual(acao["dados"]["competencias_novas"], ["Figma"])
        self.assertEqual(self.decidir(acao, "confirmar").status_code, 200)
        maria = Funcionario.objects.get(email="maria@x.com")
        self.assertEqual(sorted(c.nome for c in maria.competencias.all()), ["Figma", "Python"])

    @patch("ai.views._chamar_ollama")
    def test_email_repetido_e_avisado(self, ollama, *_):
        Funcionario.objects.create(nome="Maria", email="maria@x.com")
        ollama.return_value = chamada("cadastrar_profissional", nome="Maria", email="maria@x.com", competencias=["Python"])
        dados = self.enviar("Adicione a Maria")
        self.assertIsNone(dados["acao"])
        self.assertIn("Já existe um profissional", dados["pergunta"]["texto"])

    @patch("ai.views._chamar_ollama")
    def test_login_de_po_somente_admin_e_senha_nao_fica_no_historico(self, ollama, *_):
        ollama.return_value = chamada("cadastrar_usuario", nome="João", email="joao@x.com")
        self.assertIsNone(self.enviar("Crie um login para o João")["acao"])

        admin = self.cliente(self.admin)
        acao = self.enviar("Crie um login para o João", cliente=admin)["acao"]
        r = self.decidir(acao, "confirmar", cliente=admin).json()
        self.assertTrue(UsuarioPO.objects.get(email="joao@x.com").check_password(r["senha_temporaria"]))
        self.assertNotIn(r["senha_temporaria"], str(MensagemChat.objects.values_list("conteudo", "metadata")))

    @patch("ai.views._chamar_ollama")
    def test_cancelar_e_acao_de_outro_usuario(self, ollama, *_):
        ollama.return_value = chamada("cadastrar_competencia", nome="Kubernetes")
        acao = self.enviar("Cadastre a competência Kubernetes")["acao"]
        self.assertEqual(self.decidir(acao, "confirmar", cliente=self.cliente(self.admin)).status_code, 404)
        self.assertEqual(self.decidir(acao, "cancelar").json()["acao"]["estado"], "cancelada")
        self.assertFalse(Competencia.objects.filter(nome="Kubernetes").exists())

    @patch("ai.views._chamar_ollama")
    def test_historico_traz_pergunta_e_acao(self, ollama, *_):
        ollama.return_value = chamada("cadastrar_competencia", nome="Kubernetes")
        dados = self.enviar("Cadastre a competência Kubernetes")
        msgs = self.c.get(f"/api/conversas/{dados['conversa_id']}/mensagens/").json()["mensagens"]
        self.assertEqual(msgs[-1]["acao"]["mensagem_id"], dados["mensagem_id"])
