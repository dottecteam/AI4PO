from math import sqrt
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from pgvector.django import CosineDistance

from ai import similarity
from ai.indexing import FalhaDeEmbeddingError
from ai.models import ChunkDoc
from projects.models import Documento, Projeto
from users.models import UsuarioPO


DIMENSOES_EMBEDDING = 768
TEXTO_REQUISITO = "Como PO, desejo exportar requisitos"
TEXTOS_INVALIDOS = ("", "  \n\t", None, 123)


class SimilarityServiceUnitTests(SimpleTestCase):
    def test_constantes_publicas_refletem_a_decisao_da_task_7_1(self):
        self.assertEqual(similarity.SIMILARITY_THRESHOLD, 0.81)
        self.assertEqual(similarity.MAX_COSINE_DISTANCE, 0.19)
        self.assertEqual(similarity.MAX_SIMILAR_RESULTS, 5)
        self.assertEqual(
            similarity.MENSAGEM_POSSIVEL_SIMILARIDADE,
            "Encontramos um possível requisito semelhante.",
        )

    def test_texto_vazio_ou_nao_textual_nao_chama_embeddings(self):
        for texto in TEXTOS_INVALIDOS:
            with self.subTest(texto=texto), patch(
                "ai.similarity.gerar_embeddings"
            ) as gerar:
                self.assertIsNone(similarity.gerar_vetor_de_requisito(texto))
                gerar.assert_not_called()

    def test_remove_apenas_espacos_externos_e_reutiliza_gerador_da_indexacao(self):
        vetor = [0.1] * DIMENSOES_EMBEDDING
        with patch(
            "ai.similarity.gerar_embeddings", return_value=[vetor]
        ) as gerar:
            resultado = similarity.gerar_vetor_de_requisito(
            )

        self.assertEqual(resultado, vetor)
        gerar.assert_called_once_with(
            ["Como PO, desejo exportar requisitos."]
        )

    def test_resposta_de_embeddings_invalida_gera_falha_nomeada(self):
        vetor = [0.1] * DIMENSOES_EMBEDDING
        casos = (
            ("sem vetores", []),
            ("dois vetores", [vetor, vetor]),
            ("vetor nulo", [None]),
        )
        for caso, vetores in casos:
            with self.subTest(caso=caso), patch(
                "ai.similarity.gerar_embeddings", return_value=vetores
            ):
                with self.assertRaisesRegex(
                    FalhaDeEmbeddingError,
                ):
                    similarity.gerar_vetor_de_requisito("requisito válido")

    def test_busca_com_texto_invalido_nao_chama_embeddings_nem_banco(self):
        for texto in TEXTOS_INVALIDOS:
            with self.subTest(texto=texto), patch(
                "ai.similarity.gerar_embeddings"
            ) as gerar:
                self.assertEqual(similarity.verificar_similaridade(texto), [])
                gerar.assert_not_called()


class SimilarityPgvectorIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.vetor_consulta = [1.0] + [0.0] * (DIMENSOES_EMBEDDING - 1)
        cls.usuario = UsuarioPO.objects.create_user(
            email="po@example.com",
            nome="PO de Teste",
            password="senha-segura",
        )
        cls.projeto_a = Projeto.objects.create(
            usuario_po=cls.usuario,
            titulo="Projeto Atlas",
            descricao="Projeto de origem A",
        )
        cls.projeto_b = Projeto.objects.create(
            usuario_po=cls.usuario,
            titulo="Projeto Boreal",
            descricao="Projeto de origem B",
        )
        cls.documento_a = Documento.objects.create(
            projeto=cls.projeto_a,
            nome="atlas.md",
            tipo="md",
        )
        cls.documento_b = Documento.objects.create(
            projeto=cls.projeto_b,
            nome="boreal.md",
            tipo="md",
        )

    @staticmethod
    def _vetor_com_similaridade(similaridade):
        return [similaridade, sqrt(1.0 - similaridade**2)] + [0.0] * (
            DIMENSOES_EMBEDDING - 2
        )

    @staticmethod
    def _ids(resultados):
        return [resultado.chunk_id for resultado in resultados]

    def _criar_chunk(self, similaridade, documento=None, conteudo=None):
        documento = documento or self.documento_a
        return ChunkDoc.objects.create(
            documento=documento,
            projeto=documento.projeto,
            conteudo=conteudo or f"Requisito com similaridade {similaridade}",
            embedding=self._vetor_com_similaridade(similaridade),
        )

    def _buscar(self, texto=TEXTO_REQUISITO):
        with patch(
            "ai.similarity.gerar_embeddings",
            return_value=[self.vetor_consulta],
        ) as gerar:
            resultado = similarity.verificar_similaridade(texto)
        gerar.assert_called_once_with([texto])
        return resultado

    def test_aceita_081_e_descarta_valor_logo_abaixo_do_limiar(self):
        no_limite = self._criar_chunk(0.81)
        self._criar_chunk(0.8099)

        distancia_exata = (
            ChunkDoc.objects
            .filter(pk=no_limite.pk)
            .annotate(
                distance=CosineDistance("embedding", self.vetor_consulta)
            )
            .values_list("distance", flat=True)
            .get()
        )
        self.assertAlmostEqual(
            distancia_exata,
            similarity.MAX_COSINE_DISTANCE,
            places=6,
        )
        with patch.object(
            similarity,
            "MAX_COSINE_DISTANCE",
            distancia_exata,
        ):
            resultado = self._buscar()

        self.assertEqual(self._ids(resultado), [no_limite.id])
        self.assertAlmostEqual(resultado[0].similaridade, 0.81, places=6)

    def test_ordena_por_menor_distancia_e_retorna_a_origem(self):
        mais_distante = self._criar_chunk(
            0.90,
            documento=self.documento_a,
            conteudo="Requisito Atlas",
        )
        mais_proximo = self._criar_chunk(
            0.95,
            documento=self.documento_b,
            conteudo="Requisito Boreal",
        )

        resultado = self._buscar()

        self.assertEqual(
            self._ids(resultado),
            [mais_proximo.id, mais_distante.id],
        )
        primeiro = resultado[0]
        self.assertEqual(primeiro.conteudo, "Requisito Boreal")
        self.assertAlmostEqual(primeiro.similaridade, 0.95, places=6)
        self.assertEqual(primeiro.projeto_id, self.projeto_b.id)
        self.assertEqual(primeiro.projeto_titulo, "Projeto Boreal")
        self.assertEqual(primeiro.documento_id, self.documento_b.id)
        self.assertEqual(primeiro.documento_nome, "boreal.md")

    def test_sem_candidatos_dentro_do_limiar_devolve_lista_vazia(self):
        self._criar_chunk(0.80)

        self.assertEqual(self._buscar(), [])

    def test_empate_de_distancia_e_ordenado_pelo_id_do_chunk(self):
        primeiro = self._criar_chunk(0.90)
        segundo = self._criar_chunk(0.90)

        resultado = self._buscar()

        self.assertEqual(
            self._ids(resultado),
            [primeiro.id, segundo.id],
        )

    def test_retorna_somente_os_cinco_candidatos_mais_proximos(self):
        chunks = [
            self._criar_chunk(similaridade)
            for similaridade in (0.82, 0.83, 0.84, 0.85, 0.86, 0.87)
        ]

        resultado = self._buscar()

        self.assertEqual(len(resultado), 5)
        self.assertEqual(
            self._ids(resultado),
            [chunk.id for chunk in reversed(chunks[1:])],
        )
