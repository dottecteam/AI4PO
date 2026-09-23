from django.test import TestCase

# Create your tests here.

import tempfile
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from unittest.mock import MagicMock, patch
import requests

from ai.indexing import (
    SOBREPOSICAO_CHUNK,
    TAMANHO_MAXIMO_CHUNK,
    TAMANHO_MINIMO_CHUNK,
    FalhaDeEmbeddingError,
    dividir_em_chunks,
    gerar_embeddings,
    indexar_documento,
)

from ai.extraction import (
    ArquivoNaoEncontradoError,
    FalhaDeDecodificacaoError,
    FormatoNaoSuportadoError,
    extrair_texto,
)

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ExtracaoDeTextoTests(TestCase):
    """Caminho feliz: formatos aceitos pela task #3-1."""

    def test_extrai_texto_de_arquivo_txt(self):
        # Grava um .txt pelo default_storage (o mesmo caminho que a rota
        # de upload da #3-3 usará) e confere que o texto volta inteiro.
        default_storage.save('uploads/exemplo.txt', ContentFile(b'primeira linha\nsegunda linha'))
        self.addCleanup(default_storage.delete, 'uploads/exemplo.txt')
        texto = extrair_texto('uploads/exemplo.txt')
        self.assertEqual(texto, 'primeira linha\nsegunda linha')
    
    def test_extrai_markdown_preservando_headings(self):
        # O .md volta como está, sem strip de sintaxe: os headings ##
        # precisam sobreviver porque o chunking da #4-3 fatia por eles.
        conteudo = b'# Diario\n\n## Problema 1\nDescricao do problema.\n'
        default_storage.save('uploads/diario.md', ContentFile(conteudo))
        self.addCleanup(default_storage.delete, 'uploads/diario.md')
        texto = extrair_texto('uploads/diario.md')
        self.assertIn('# Diario', texto)
        self.assertIn('## Problema 1', texto)

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ErrosDeExtracaoTests(TestCase):
    """Os três modos de falha do módulo, um por exceção nomeada."""

    def test_formato_fora_da_lista_levanta_erro(self):
        # .pdf ficou fora do escopo da Sprint 1 (decisão da #3-1).
        with self.assertRaises(FormatoNaoSuportadoError):
            extrair_texto('uploads/atestado.pdf')

    def test_caminho_inexistente_levanta_erro(self):
        # Extensão válida, mas o arquivo nunca foi enviado ao storage.
        with self.assertRaises(ArquivoNaoEncontradoError):
            extrair_texto('uploads/nao-existe.txt')

    def test_binario_disfarcado_de_texto_levanta_erro(self):
        # Bytes que não são UTF-8 válido (0xff não aparece em texto UTF-8).
        default_storage.save('uploads/falso.txt', ContentFile(b'\xff\xfe\x00\x01'))
        self.addCleanup(default_storage.delete, 'uploads/falso.txt')
        with self.assertRaises(FalhaDeDecodificacaoError):
            extrair_texto('uploads/falso.txt')

class ChunkingTests(TestCase):
    """Testes de dividir_em_chunks: contrato Chunk, headings, teto e overlap."""

    def test_documento_vazio_devolve_lista_vazia(self):
        self.assertEqual(dividir_em_chunks(''), [])
        self.assertEqual(dividir_em_chunks('   \n  '), [])

    def test_texto_sem_headings_vira_chunk_unico(self):
        texto = 'intro sem nenhum heading'
        chunks = dividir_em_chunks(texto)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].texto, texto)
        self.assertIsNone(chunks[0].caminho_heading)
        self.assertEqual(chunks[0].indice, 0)

    def test_cada_heading_abre_um_chunk_com_ele_dentro(self):
        texto = '# A\nconteudo a\n## B\nconteudo b\n### C\nconteudo c'
        chunks = dividir_em_chunks(texto)
        self.assertEqual(len(chunks), 3)
        self.assertTrue(chunks[0].texto.startswith('# A'))
        self.assertTrue(chunks[1].texto.startswith('## B'))
        self.assertTrue(chunks[2].texto.startswith('### C'))
        self.assertEqual(
            [c.caminho_heading for c in chunks], ['A', 'A > B', 'A > B > C'],
        )

    def test_secao_maior_que_o_teto_e_fatiada_com_margem_de_absorcao(self):
        secao = '## Grande\n' + ('palavra ' * 20 + '\n') * 30
        chunks = dividir_em_chunks(secao)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(chunks[0].texto.startswith('## Grande'))
        for chunk in chunks:
            self.assertLessEqual(
                len(chunk.texto), TAMANHO_MAXIMO_CHUNK + TAMANHO_MINIMO_CHUNK,
            )

    def test_intro_e_ordem_das_secoes_preservadas(self):
        texto = 'intro antes de tudo\n# Um\num\n# Dois\ndois'
        chunks = dividir_em_chunks(texto)
        self.assertEqual(
            [(c.texto, c.caminho_heading) for c in chunks],
            [('intro antes de tudo', None), ('# Um\num', 'Um'), ('# Dois\ndois', 'Dois')],
        )
        self.assertEqual([c.indice for c in chunks], [0, 1, 2])

    def test_caminho_hierarquico_acumula_pais_e_reseta_irmaos(self):
        texto = '# Seg\ntopo\n## EPIs\nconteudo\n## Luvas\noutro'
        caminhos = [c.caminho_heading for c in dividir_em_chunks(texto)]
        self.assertEqual(caminhos, ['Seg', 'Seg > EPIs', 'Seg > Luvas'])

    def test_sobreposicao_repete_a_fronteira_entre_chunks(self):
        texto = '## Linha\n' + 'palavra ' * 400
        chunks = dividir_em_chunks(texto)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(
            chunks[0].texto[-SOBREPOSICAO_CHUNK:],
            chunks[1].texto[:SOBREPOSICAO_CHUNK],
        )

    def test_sobra_curta_e_absorvida_sem_chunk_minusculo(self):
        texto = 'palavra ' * 124 + 'cauda final'
        chunks = dividir_em_chunks(texto)
        self.assertEqual(len(chunks), 1)
        self.assertGreater(len(chunks[0].texto), TAMANHO_MAXIMO_CHUNK)
        self.assertTrue(chunks[0].texto.endswith('cauda final'))

    def test_texto_para_embedding_inclui_caminho_quando_existe(self):
        chunks = dividir_em_chunks('# Seg\ntopo\n## EPIs\nconteudo')
        self.assertEqual(
            chunks[0].texto_para_embedding, '[Seg]\n# Seg\ntopo',
            )
        intro = dividir_em_chunks('intro pura')[0]
        self.assertEqual(intro.texto_para_embedding, 'intro pura')


class EmbeddingsTests(TestCase):
    """Testes de gerar_embeddings: batch, atalho e falha nomeada."""

    def test_gera_vetores_em_uma_unica_chamada_batch(self):
        vetores = [[0.1, 0.2], [0.3, 0.4]]
        with patch('ai.indexing.requests.post') as post_falso:
            post_falso.return_value.json.return_value = {'embeddings': vetores}
            resultado = gerar_embeddings(['texto a', 'texto b'])
        self.assertEqual(resultado, vetores)
        post_falso.assert_called_once()
        _, kwargs = post_falso.call_args
        self.assertEqual(kwargs['json']['input'], ['texto a', 'texto b'])

    def test_lista_vazia_devolve_lista_vazia_sem_chamar_ollama(self):
        with patch('ai.indexing.requests.post') as post_falso:
            self.assertEqual(gerar_embeddings([]), [])
        post_falso.assert_not_called()

    def test_ollama_fora_do_ar_vira_falha_nomeada(self):
        with patch('ai.indexing.requests.post',
                   side_effect=requests.exceptions.ConnectionError('recusada')):
            with self.assertRaises(FalhaDeEmbeddingError):
                gerar_embeddings(['texto'])

    def test_resposta_sem_embeddings_vira_falha_nomeada(self):
        with patch('ai.indexing.requests.post') as post_falso:
            post_falso.return_value.json.return_value = {'error': 'modelo ausente'}
            with self.assertRaises(FalhaDeEmbeddingError):
                gerar_embeddings(['texto'])
            

class IndexacaoDeDocumentoTests(TestCase):
    """Testes de indexar_documento: orquestração com tudo mockado."""

    def test_pipeline_completo_casa_chunks_com_vetores_e_grava_em_lote(self):
        documento = MagicMock()
        documento.arquivo.name = 'uploads/doc.md'
        documento.projeto = 'PayCore'
        vetores = [[0.1] * 768, [0.2] * 768]
        with patch('ai.indexing.extrair_texto',
                   return_value='# A\naaa\n# B\nbbb') as extrair, \
             patch('ai.indexing.gerar_embeddings', return_value=vetores) as gerar, \
             patch('ai.indexing.ChunkDoc') as modelo:
            quantidade = indexar_documento(documento)

        self.assertEqual(quantidade, 2)
        extrair.assert_called_once_with('uploads/doc.md')
        gerar.assert_called_once_with(['[A]\n# A\naaa', '[B]\n# B\nbbb'])
        modelo.objects.bulk_create.assert_called_once()
        (registros,), _ = modelo.objects.bulk_create.call_args
        self.assertEqual(len(registros), 2)
        primeiro = modelo.call_args_list[0].kwargs
        self.assertEqual(primeiro['documento'], documento)
        self.assertEqual(primeiro['projeto'], 'PayCore')
        self.assertEqual(primeiro['embedding'], vetores[0])

    def test_documento_vazio_devolve_zero_sem_chamar_ollama_nem_banco(self):
        documento = MagicMock()
        documento.arquivo.name = 'uploads/vazio.md'
        with patch('ai.indexing.extrair_texto', return_value=''), \
             patch('ai.indexing.gerar_embeddings') as gerar, \
             patch('ai.indexing.ChunkDoc') as modelo:
            self.assertEqual(indexar_documento(documento), 0)
        gerar.assert_not_called()
        modelo.objects.bulk_create.assert_not_called()

    def test_divergencia_entre_chunks_e_vetores_vira_falha_nomeada(self):
        documento = MagicMock()
        documento.arquivo.name = 'uploads/doc.md'
        with patch('ai.indexing.extrair_texto', return_value='# A\naaa\n# B\nbbb'), \
             patch('ai.indexing.gerar_embeddings', return_value=[[0.1] * 768]):
            with self.assertRaises(FalhaDeEmbeddingError):
                indexar_documento(documento)
