from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from ai.indexing import FalhaDeEmbeddingError
from ai.similarity import ResultadoSimilaridade


class SimilarityCheckViewTests(SimpleTestCase):
    url = "/api/similarity/"

    def setUp(self):
        self.client = APIClient()
        verificar = patch("ai.similarity.verificar_similaridade")
        self.verificar = verificar.start()
        self.addCleanup(verificar.stop)

    def test_post_serializa_camel_case_e_origem(self):
        self.verificar.return_value = [
            ResultadoSimilaridade(
                chunk_id=42,
                conteudo="O cliente poderá solicitar um link de recuperação.",
                similaridade=0.872341,
                projeto_id=3,
                projeto_titulo="Portal do Cliente",
                documento_id=8,
                documento_nome="requisitos-autenticacao.pdf",
            )
        ]
        texto = "Como cliente, quero recuperar meu acesso."

        response = self.client.post(self.url, {"texto": texto}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resultados": [
                    {
                        "chunkId": 42,
                        "conteudo": "O cliente poderá solicitar um link de recuperação.",
                        "similaridade": 0.872341,
                        "projeto": {"id": 3, "titulo": "Portal do Cliente"},
                        "documento": {
                            "id": 8,
                            "nome": "requisitos-autenticacao.pdf",
                        },
                    }
                ]
            },
        )
        self.verificar.assert_called_once_with(texto)

    def test_preserva_ordem_dos_resultados_do_servico(self):
        self.verificar.return_value = [
            ResultadoSimilaridade(91, "Primeiro", 0.93, 2, "B", 5, "b.md"),
            ResultadoSimilaridade(12, "Segundo", 0.88, 1, "A", 4, "a.md"),
        ]

        response = self.client.post(
            self.url, {"texto": "Requisito válido"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["chunkId"] for item in response.json()["resultados"]],
            [91, 12],
        )

    def test_texto_vazio_ou_so_espacos_retorna_lista_vazia(self):
        for texto in ("", "  \n\t"):
            with self.subTest(texto=texto):
                response = self.client.post(
                    self.url, {"texto": texto}, format="json"
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"resultados": []})
        self.verificar.assert_not_called()

    def test_ausencia_de_texto_retorna_400(self):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"detail": "O campo texto deve ser uma string."}
        )
        self.verificar.assert_not_called()

    def test_tipo_nao_textual_retorna_400(self):
        for texto in (None, 123, False, [], {}):
            with self.subTest(texto=texto):
                response = self.client.post(
                    self.url, {"texto": texto}, format="json"
                )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json(),
                    {"detail": "O campo texto deve ser uma string."},
                )
        self.verificar.assert_not_called()

    def test_sem_correspondencias_retorna_lista_vazia(self):
        self.verificar.return_value = []

        response = self.client.post(
            self.url, {"texto": "Requisito sem correspondência"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"resultados": []})

    def test_falha_de_embeddings_retorna_503_sem_detalhes_internos(self):
        self.verificar.side_effect = FalhaDeEmbeddingError("detalhe interno")

        response = self.client.post(
            self.url, {"texto": "Requisito válido"}, format="json"
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Verificação de similaridade indisponível."},
        )

    def test_get_retorna_405(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.verificar.assert_not_called()
