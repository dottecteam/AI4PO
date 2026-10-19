from django.test import TestCase

# Create your tests here.

import json
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

from ai.graphrag import (
    _chave_identidade,
    _nome_melhor,
    _termos_da_pergunta,
    buscar_no_grafo,
)
from ai.models import ChunkDoc, Comunidade, Entidade, Relacao
from projects.models import Documento, Projeto
from users.models import UsuarioPO

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


# ---------------------------------------------------------------------------
# GraphRAG (tasks #13-1 a #13-3): identidade de nós e retrieval no grafo.
# ---------------------------------------------------------------------------

class IdentidadeDeNoTests(TestCase):
    """Canonização sem dicionário de apelidos: handle e nome real são o mesmo nó."""

    def test_handle_e_nome_real_colapsam_na_mesma_chave(self):
        self.assertEqual(_chave_identidade('kayanmatta'), _chave_identidade('Kayan da Matta'))
        self.assertEqual(_chave_identidade('KauanDomingues'), _chave_identidade('Kauan Domingues'))

    def test_pessoas_diferentes_nao_colapsam(self):
        self.assertNotEqual(_chave_identidade('João Paulo'), _chave_identidade('Paulo João'))
        self.assertNotEqual(_chave_identidade('frontend do AI4PO'), _chave_identidade('frontend'))

    def test_rotulo_legivel_vence_o_handle(self):
        self.assertTrue(_nome_melhor('Kayan da Matta', 'kayanmatta'))
        self.assertFalse(_nome_melhor('kayanmatta', 'Kayan da Matta'))

    def test_termos_miudos_foram_descartados_da_busca(self):
        # A pergunta passa pela MESMA normalização dos nós: 'embeddings' vira
        # 'embedding' aqui e no nome do nó, e é isso que faz os dois se acharem.
        termos = _termos_da_pergunta('Quem é o dono da pipeline de embeddings?')
        self.assertIn('pipeline', termos)
        self.assertIn('embedding', termos)
        for miuda in ('o', 'da', 'de', 'e'):
            self.assertNotIn(miuda, termos)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class RetrievalNoGrafoTests(TestCase):
    """O grafo responde pergunta de relacionamento, dentro de um único projeto."""

    def setUp(self):
        po = UsuarioPO.objects.create_user(email='po@pro4tech.com', nome='PO', password='x')
        self.projeto = Projeto.objects.create(usuario_po=po, titulo='PayCore', descricao='pagamentos')
        outro = UsuarioPO.objects.create_user(email='outro@pro4tech.com', nome='Outro', password='x')
        self.projeto_alheio = Projeto.objects.create(usuario_po=outro, titulo='RealIT', descricao='credito')

        documento = Documento.objects.create(projeto=self.projeto, nome='atas.md', tipo='md')
        self.chunk = ChunkDoc.objects.create(
            documento=documento, projeto=self.projeto,
            conteudo='Marya entregou o frontend do chatbot.', embedding=[0.0] * 768,
        )

        marya = self._no('Marya Vitória', 'pessoa', self.projeto, 'Desenvolvedora do time')
        frontend = self._no('frontend do chatbot', 'artefato', self.projeto, 'Interface do chatbot')
        decisao = self._no('Decisão de layout', 'decisao', self.projeto, 'Definida na sprint 2')
        self._aresta(marya, frontend, 'implementa', 0.9)
        self._aresta(frontend, decisao, 'deriva_de', 0.7)

        comunidade = Comunidade.objects.create(
            projeto=self.projeto, titulo='Entregas de interface',
            resumo='Agrupa o frontend e quem o construiu.', tamanho=2,
        )
        comunidade.membros.set([marya, frontend])

        analista = self._no('Renata Prado', 'pessoa', self.projeto_alheio, 'Analista de crédito')
        self._aresta(analista, self._no('Cooperativa Vale Norte', 'sistema', self.projeto_alheio), 'pertence_a', 0.8)

    def _no(self, nome, tipo, projeto, descricao=''):
        return Entidade.objects.create(
            nome=nome, chave=_chave_identidade(nome), tipo=tipo, descricao=descricao, projeto=projeto,
        )

    def _aresta(self, origem, destino, tipo, confianca):
        aresta = Relacao.objects.create(
            origem=origem, destino=destino, tipo=tipo, confianca=confianca, projeto=self.projeto,
        )
        aresta.evidencias.add(self.chunk)
        return aresta

    def test_pergunta_de_relacionamento_traz_pessoa_e_artefato(self):
        resposta = buscar_no_grafo('quem implementou o frontend do chatbot?', self.projeto.id)
        self.assertIn('Marya Vitória', resposta)
        self.assertIn('frontend do chatbot', resposta)
        self.assertIn('implementa', resposta)

    def test_um_salto_alcancia_a_decisao_por_tras_do_artefato(self):
        resposta = buscar_no_grafo('frontend do chatbot', self.projeto.id, max_saltos=1)
        self.assertIn('Decisão de layout', resposta)

    def test_salto_zero_mostra_so_a_vizinhanca_imediata(self):
        resposta = buscar_no_grafo('frontend do chatbot', self.projeto.id, max_saltos=0)
        self.assertNotIn('Decisão de layout', resposta)

    def test_comunidade_e_fonte_aparecem_no_contexto(self):
        resposta = buscar_no_grafo('frontend do chatbot', self.projeto.id)
        self.assertIn('Entregas de interface', resposta)
        self.assertIn('atas.md', resposta)

    def test_nao_vaza_para_o_grafo_de_outro_projeto(self):
        resposta = buscar_no_grafo('Renata Prado', self.projeto.id)
        self.assertNotIn('Renata Prado', resposta)
        self.assertIn('Nenhuma entidade', resposta)
        self.assertIn('Renata Prado', buscar_no_grafo('Renata Prado', self.projeto_alheio.id))

    def test_sem_projeto_nao_consulta_nada(self):
        self.assertTrue(buscar_no_grafo('frontend do chatbot', None).startswith('Nenhuma pergunta'))

    def test_aresta_de_confianca_baixa_nao_colapara_temas(self):
        # CONF_MINIMA é a mesma régua do desenho e das comunidades.
        Relacao.objects.filter(projeto_id=self.projeto.id).update(confianca=0.1)
        resposta = buscar_no_grafo('frontend do chatbot', self.projeto.id)
        self.assertNotIn('Marya Vitória', resposta)


class FerramentaDoGrafoNaViewTests(TestCase):
    """Prova a ligação view → grafo: sem isto a #13-3 é só uma função órfã."""

    def setUp(self):
        po = UsuarioPO.objects.create_user(email='view@pro4tech.com', nome='PO View', password='x')
        self.projeto = Projeto.objects.create(usuario_po=po, titulo='PayCore', descricao='pagamentos')
        marya = Entidade.objects.create(nome='Marya Vitória', chave='maryavitoria', tipo='pessoa',
                                        descricao='Desenvolvedora', projeto=self.projeto)
        frontend = Entidade.objects.create(nome='frontend do chatbot', chave='frontendchatbot',
                                           tipo='artefato', descricao='Interface', projeto=self.projeto)
        Relacao.objects.create(origem=marya, destino=frontend, tipo='implementa',
                               confianca=0.9, projeto=self.projeto)

    def _resposta(self, conteudo):
        mock = MagicMock()
        mock.raise_for_status.return_value = None
        mock.json.return_value = {"message": conteudo}
        return mock

    def test_agente_aciona_ferramenta_e_recebe_contexto_do_grafo(self):
        depois_de_ferramenta = self._resposta({"content": "Foi a Marya Vitória."})
        with patch('ai.views.requests.post', side_effect=[
            self._resposta({"tool_calls": [{"function": {
                "name": "consultar_grafo_conhecimento",
                "arguments": {"pergunta": "quem fez o frontend do chatbot?"},
            }}]}),
            depois_de_ferramenta,
        ]) as post:
            resposta = self.client.post(
                '/api/chat/',
                json.dumps({'message': 'quem fez o frontend do chatbot?', 'projeto_id': self.projeto.id}),
                content_type='application/json',
            )

        self.assertEqual(resposta.status_code, 200)
        mensagens = post.call_args_list[1].kwargs["json"]["messages"]
        conteudo_da_ferramenta = [m for m in mensagens if m.get("role") == "tool"]
        self.assertEqual(len(conteudo_da_ferramenta), 1)
        self.assertIn('Marya Vitória', conteudo_da_ferramenta[0]["content"])
        self.assertIn('implementa', conteudo_da_ferramenta[0]["content"])

    def test_ferramenta_nao_le_grafo_de_outro_projeto(self):
        outro_po = UsuarioPO.objects.create_user(email='outro@pro4tech.com', nome='Outro PO', password='x')
        outro = Projeto.objects.create(usuario_po=outro_po, titulo='RealIT', descricao='crédito')
        Entidade.objects.create(nome='Renata Prado', chave='renataprado', tipo='pessoa',
                                descricao='Analista de crédito', projeto=outro)

        with patch('ai.views.requests.post', side_effect=[
            self._resposta({"tool_calls": [{"function": {
                "name": "consultar_grafo_conhecimento",
                "arguments": {"pergunta": "quem é Renata Prado?"},
            }}]}),
            self._resposta({"content": "Não consta no projeto."}),
        ]) as post:
            self.client.post(
                '/api/chat/',
                json.dumps({'message': 'quem é Renata Prado?', 'projeto_id': self.projeto.id}),
                content_type='application/json',
            )

        mensagens = post.call_args_list[1].kwargs["json"]["messages"]
        conteudo = [m for m in mensagens if m.get("role") == "tool"][0]["content"]
        self.assertNotIn('Renata Prado', conteudo)
