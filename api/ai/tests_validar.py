from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

ESPEC_CONFORME = {
    "epicos": [{
        "titulo": "Gestão de acesso de usuários",
        "descricao": "Permitir que membros do time acessem o sistema de forma controlada e rastreável.",
        "objetivo": "Garantir que somente pessoas autorizadas utilizem as funcionalidades do sistema.",
        "escopo_macro": ["Cadastro de usuários", "Autenticação de usuários"],
        "resultado_esperado": "Usuários conseguem criar conta e entrar no sistema com segurança.",
        "criterios_aceitacao": [
            "Todo usuário cadastrado consegue entrar no sistema.",
            "Usuários não autorizados não acessam as funcionalidades.",
        ],
        "features": [{
            "titulo": "Autenticação de usuários",
            "descricao": "Permitir o registro e a entrada de usuários mediante credenciais próprias.",
            "objetivo": "Identificar cada usuário antes de liberar o acesso.",
            "criterios_aceitacao": [
                "Credenciais inválidas impedem o acesso.",
                "Senhas são armazenadas de forma protegida.",
            ],
            "pbis": [
                {
                    "titulo": "Cadastrar usuário",
                    "historia": "Como membro do time, eu quero criar minha conta, para que eu possa acessar o sistema.",
                    "cenarios": [
                        {"nome": "Cadastro com dados válidos",
                         "dado": "que o usuário informa nome, e-mail e senha válidos",
                         "quando": "ele confirma o cadastro",
                         "entao": "a conta é criada e uma mensagem de sucesso é exibida"},
                        {"nome": "Cadastro com senha inválida",
                         "dado": "que o usuário informa uma senha inválida",
                         "quando": "ele confirma o cadastro",
                         "entao": "o cadastro é recusado e o sistema informa o erro"},
                    ],
                },
                {
                    "titulo": "Autenticar usuário",
                    "historia": "Como usuário cadastrado, eu quero entrar no sistema com minhas credenciais, para que eu acesse minhas funcionalidades.",
                    "cenarios": [
                        {"nome": "Entrada com credenciais cadastradas",
                         "dado": "que o usuário possui conta ativa",
                         "quando": "ele informa as credenciais cadastradas",
                         "entao": "o acesso é liberado"},
                        {"nome": "Entrada com senha inválida",
                         "dado": "que o usuário informa uma senha inválida",
                         "quando": "ele tenta entrar",
                         "entao": "o acesso é negado e uma mensagem de erro é exibida"},
                    ],
                },
            ],
        }],
    }]
}

ESPEC_INCOMPLETA = {"epicos": [{"titulo": "Gestão de acesso"}]}


def regras_com_falha(res):
    return {p["regra"] for p in res.data["pendencias"] if not p["ok"]}


class ValidarEspecificacaoTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="a@a.com", nome="Usuário A", password="123456")
        self.client = APIClient()
        self.url = reverse("validar-especificacao")

    def test_exige_login(self):
        res = self.client.post(self.url, ESPEC_CONFORME, format="json")
        self.assertIn(res.status_code, (401, 403))

    def test_rejeita_corpo_que_nao_e_objeto(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(self.url, [], format="json")
        self.assertEqual(res.status_code, 400)

    def test_rejeita_sem_lista_de_epicos(self):
        self.client.force_authenticate(self.user)
        for corpo in ({}, {"epicos": "texto"}):
            res = self.client.post(self.url, corpo, format="json")
            self.assertEqual(res.status_code, 400)

    def test_especificacao_conforme(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(self.url, ESPEC_CONFORME, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["conforme"], res.data["erros"])  #mostra os erros se falhar
        self.assertEqual(res.data["erros"], [])

    def test_especificacao_incompleta_lista_pendencias(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(self.url, ESPEC_INCOMPLETA, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data["conforme"])
        falhas = regras_com_falha(res)
        self.assertIn("EPICO-CAMPO-DESCRICAO", falhas)
        self.assertIn("EPICO-DECOMPOSICAO-FEATURES", falhas)