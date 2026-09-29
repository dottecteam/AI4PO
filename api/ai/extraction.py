"""Extração de texto de documentos enviados (task #4-2).

Primeira etapa do pipeline de indexação: converte arquivos `.md`/`.txt`
gravados no storage (contrato da #3-4) em texto UTF-8. A #4-3 consome
``extrair_texto`` com esta assinatura; não toca em banco, rota ou chunking.
"""

from django.core.files.storage import default_storage

# Formatos aceitos na Sprint 1 (decisão da #3-1).
FORMATOS_SUPORTADOS = ('.md', '.txt')


class FormatoNaoSuportadoError(Exception):
    """Extensão fora de FORMATOS_SUPORTADOS."""


class ArquivoNaoEncontradoError(Exception):
    """Caminho não existe no storage."""


class FalhaDeDecodificacaoError(Exception):
    """Conteúdo não é texto UTF-8 válido."""


def extrair_texto(caminho_no_storage):
    """Devolve o conteúdo do arquivo como texto UTF-8.

    Recebe caminho relativo ao MEDIA_ROOT (ex.: ``uploads/abc123.md``).
    O `.md` volta sem strip de markdown: os headings alimentam o chunking
    da #4-3. Levanta FormatoNaoSuportadoError, ArquivoNaoEncontradoError
    ou FalhaDeDecodificacaoError.
    """
    # Extensão primeiro: rejeita upload errado antes de qualquer leitura.
    if not caminho_no_storage.lower().endswith(FORMATOS_SUPORTADOS):
        raise FormatoNaoSuportadoError(
            f'Formato não suportado: {caminho_no_storage}. '
            f'Aceitos: {", ".join(FORMATOS_SUPORTADOS)}.'
        )

    # default_storage: hoje disco local, amanhã nuvem, sem mudar esta chamada.
    if not default_storage.exists(caminho_no_storage):
        raise ArquivoNaoEncontradoError(
            f'Arquivo não existe no storage: {caminho_no_storage}.'
        )

    # Leitura binária: a decodificação é responsabilidade deste módulo.
    with default_storage.open(caminho_no_storage, 'rb') as arquivo:
        conteudo = arquivo.read()

    try:
        return conteudo.decode('utf-8')
    except UnicodeDecodeError as erro:
        raise FalhaDeDecodificacaoError(
            f'Conteúdo de {caminho_no_storage} não é texto UTF-8 válido.'
        ) from erro
