from django.test import TestCase

# Create your tests here.

import tempfile

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings

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