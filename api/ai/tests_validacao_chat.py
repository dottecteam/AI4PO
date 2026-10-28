from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .checklist import resumo_validacao
from .models import Conversa
from .parser_especificacao import extrair_especificacao, parece_especificacao

TEXTO_CONFORME = """Épico: Gestão de acesso de usuários
Descrição: Permitir que membros do time acessem o sistema de forma controlada e rastreável.
Objetivo: Garantir que somente pessoas autorizadas utilizem as funcionalidades do sistema.
Escopo macro:
- Cadastro de usuários
- Autenticação de usuários
Resultado esperado: Usuários conseguem criar conta e entrar no sistema com segurança.
Critérios de aceitação:
- Todo usuário cadastrado consegue entrar no sistema.
- Usuários não autorizados não acessam as funcionalidades.

Feature: Autenticação de usuários
Descrição: Permitir o registro e a entrada de usuários mediante credenciais próprias.
Objetivo: Identificar cada usuário antes de liberar o acesso.
Critérios de aceitação:
- Credenciais inválidas impedem o acesso.
- Senhas são armazenadas de forma protegida.

PBI: Cadastrar usuário
História: Como membro do time, eu quero criar minha conta, para que eu possa acessar o sistema.
Cenário: Cadastro com dados válidos
Dado: que o usuário informa nome, e-mail e senha válidos
Quando: ele confirma o cadastro
Então: a conta é criada e uma mensagem de sucesso é exibida
Cenário: Cadastro com senha inválida
Dado: que o usuário informa uma senha inválida
Quando: ele confirma o cadastro
Então: o cadastro é recusado e o sistema informa o erro

PBI: Autenticar usuário
História: Como usuário cadastrado, eu quero entrar no sistema com minhas credenciais, para que eu acesse minhas funcionalidades.
Cenário: Entrada com credenciais cadastradas
Dado: que o usuário possui conta ativa
Quando: ele informa as credenciais cadastradas
Então: o acesso é liberado
Cenário: Entrada com senha inválida
Dado: que o usuário informa uma senha inválida
Quando: ele tenta entrar
Então: o acesso é negado e uma mensagem de erro é exibida
"""


class ParserEspecificacaoTests(SimpleTestCase):
    def test_estrutura_extraida(self):
        dados, obs = extrair_especificacao(TEXTO_CONFORME)
        self.assertEqual(obs, [])
        self.assertEqual(len(dados["epicos"]), 1)
        epico = dados["epicos"][0]
        self.assertEqual(epico["titulo"], "Gestão de acesso de usuários")
        self.assertEqual(len(epico["escopo_macro"]), 2)
        self.assertEqual(len(epico["criterios_aceitacao"]), 2)
        feature = epico["features"][0]
        self.assertEqual(len(feature["pbis"]), 2)
        pbi = feature["pbis"][0]
        self.assertEqual(pbi["titulo"], "Cadastrar usuário")
        self.assertEqual(len(pbi["cenarios"]), 2)
        self.assertEqual(
            pbi["cenarios"][1]["entao"],
            "o cadastro é recusado e o sistema informa o erro",
        )

    def test_texto_conforme_passa_no_checklist(self):
        dados, _ = extrair_especificacao(TEXTO_CONFORME)
        resumo = resumo_validacao(dados)
        self.assertTrue(resumo["conforme"], resumo["erros"])

    def test_especificacao_incompleta_gera_pendencias(self):
        dados, _ = extrair_especificacao("Épico: Gestão de acesso\nFeature: Autenticação")
        falhas = {p["regra"] for p in resumo_validacao(dados)["pendencias"] if not p["ok"]}
        self.assertIn("EPICO-CAMPO-DESCRICAO", falhas)
        self.assertIn("FEATURE-DECOMPOSICAO-PBIS", falhas)

    def test_gherkin_sem_dois_pontos(self):
        texto = (
            "PBI: Cadastrar usuário\n"
            "Cenário: Cadastro válido\n"
            "Dado que o usuário informa dados válidos\n"
            "Quando ele confirma\n"
            "Então a conta é criada\n"
        )
        dados, _ = extrair_especificacao(texto)
        cenario = dados["epicos"][0]["features"][0]["pbis"][0]["cenarios"][0]
        self.assertEqual(cenario["nome"], "Cadastro válido")
        self.assertEqual(cenario["dado"], "que o usuário informa dados válidos")
        self.assertEqual(cenario["quando"], "ele confirma")
        self.assertEqual(cenario["entao"], "a conta é criada")

    def test_cenario_em_uma_linha_vira_criterio_em_texto(self):
        texto = (
            "PBI: Entrar no sistema\n"
            "Dado que o usuário está cadastrado, quando ele informa a senha, "
            "então o acesso é liberado\n"
        )
        dados, _ = extrair_especificacao(texto)
        pbi = dados["epicos"][0]["features"][0]["pbis"][0]
        self.assertEqual(pbi["cenarios"], [])
        self.assertEqual(len(pbi["criterios_aceitacao"]), 1)

    def test_campo_em_varias_linhas(self):
        texto = (
            "PBI: Cadastrar usuário\n"
            "História: Como membro do time, eu quero criar minha conta,\n"
            "para que eu possa acessar o sistema.\n"
        )
        dados, _ = extrair_especificacao(texto)
        pbi = dados["epicos"][0]["features"][0]["pbis"][0]
        self.assertEqual(
            pbi["historia"],
            "Como membro do time, eu quero criar minha conta, "
            "para que eu possa acessar o sistema.",
        )

    def test_cenario_fora_de_pbi_gera_observacao(self):
        _, obs = extrair_especificacao("Épico: A\nCenário: solto")
        self.assertTrue(any("fora de um PBI" in o for o in obs))

    def test_nada_reconhecido(self):
        dados, _ = extrair_especificacao("oi, tudo bem?")
        self.assertEqual(dados["epicos"], [])

    def test_parece_especificacao(self):
        self.assertTrue(parece_especificacao("Feature: login\nDescrição: acesso ao sistema"))
        self.assertFalse(parece_especificacao("Feature: login"))
        self.assertFalse(parece_especificacao("Olá, preciso de ajuda com requisitos"))
        self.assertFalse(parece_especificacao("Descrição: algo\nObjetivo: outra coisa"))


class ChatValidacaoTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="a@a.com", nome="Usuário A", password="123456")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = reverse("chat")

    def enviar(self, message):
        return self.client.post(self.url, {"message": message}, format="json")

    def test_especificacao_conforme_vira_cartao(self):
        res = self.enviar(TEXTO_CONFORME)
        self.assertEqual(res.status_code, 200)
        dados = res.json()
        validacao = dados["validacao"]
        self.assertTrue(validacao["conforme"], validacao["erros"])
        self.assertEqual(validacao["erros"], [])

        conversa = Conversa.objects.get(pk=dados["conversa_id"])
        self.assertEqual(conversa.usuario_po, self.user)
        self.assertEqual(conversa.titulo, "Validação de especificação")
        mensagens = list(conversa.mensagens.all())
        self.assertEqual([m.papel for m in mensagens], ["user", "assistant"])
        self.assertIn("conformidade", mensagens[1].conteudo)

    def test_especificacao_incompleta_lista_pendencias(self):
        res = self.enviar("/validar\nÉpico: Gestão de acesso")
        self.assertEqual(res.status_code, 200)
        validacao = res.json()["validacao"]
        self.assertFalse(validacao["conforme"])
        regras = {e["regra"] for e in validacao["erros"]}
        self.assertIn("EPICO-CAMPO-DESCRICAO", regras)

    def test_comando_sem_texto_devolve_o_modelo(self):
        res = self.enviar("/validar")
        self.assertEqual(res.status_code, 200)
        dados = res.json()
        self.assertIsNone(dados["validacao"])
        self.assertIn("Épico:", dados["message"])

    @patch("ai.views.requests.post")
    def test_mensagem_comum_continua_indo_para_o_ollama(self, mock_post):
        mock_post.return_value.json.return_value = {"message": {"content": "Olá!"}}
        res = self.enviar("Oi, tudo bem?")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("validacao", res.json())
        self.assertTrue(mock_post.called)