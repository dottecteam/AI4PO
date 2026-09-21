"""Pipeline de indexação de documentos (task #4-3).

Segunda etapa do fluxo RAG: recebe o texto extraído pela #4-2 e fatia em
chunks; nas etapas seguintes gera embeddings via Ollama e grava no
pgvector. Não toca em rota nem em banco por conta própria.
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from ai.extraction import extrair_texto
from ai.models import ChunkDoc

import requests
from decouple import config

# Teto de caracteres por chunk: equilibra contexto rico vs. precisão da busca.
TAMANHO_MAXIMO_CHUNK = 1000

# Quantos caracteres do fim de um chunk se repetem no início do próximo,
# dentro da mesma seção — evita perder informação cortada bem na fronteira.
SOBREPOSICAO_CHUNK = 150

# Sobra menor que isso não vira chunk próprio: é absorvida pelo pedaço
# anterior, que pode passar do teto em até este valor.
TAMANHO_MINIMO_CHUNK = 80

_RE_HEADING = re.compile(r'^(#{1,6})\s+(.+)')


@dataclass
class Chunk:
    """Um chunk pronto pra embedding, com o contexto hierárquico preservado."""
    texto: str                       # trecho original da seção, linha do heading inclusa
    caminho_heading: Optional[str]   # ex.: "Segurança > EPIs > Capacete"
    indice: int                      # posição do chunk no documento (0-based)

    @property
    def texto_para_embedding(self) -> str:
        """Texto que deve ir pro modelo de embedding: contexto + conteúdo.

        Prependar o caminho do heading ajuda a busca semântica a distinguir
        chunks de conteúdo parecido que vivem sob títulos diferentes.
        """
        if not self.caminho_heading:
            return self.texto
        return f'[{self.caminho_heading}]\n{self.texto}'


def _atualizar_pilha_headings(pilha, nivel, titulo):
    """Empilha o heading atual, descartando os de nível igual ou mais profundo.

    Isso mantém o caminho hierárquico correto: um novo `##` fecha o `##`
    anterior mas preserva o `#` pai; um novo `#` reseta tudo.
    """
    while pilha and pilha[-1][0] >= nivel:
        pilha.pop()
    pilha.append((nivel, titulo))
    return pilha


def _caminho_heading(pilha):
    return ' > '.join(titulo for _, titulo in pilha) if pilha else None


def _melhor_ponto_de_corte(texto, teto):
    """Acha onde cortar <= teto, preferindo parágrafo > linha > espaço > corte duro."""
    if len(texto) <= teto:
        return len(texto)
    for separador in ('\n\n', '\n', ' '):
        corte = texto.rfind(separador, 0, teto)
        if corte > 0:
            return corte
    return teto


def _dividir_secao(texto):
    """Fatia o texto de uma seção em pedaços <= teto, com sobreposição entre eles."""
    texto = texto.strip('\n')
    if not texto:
        return []

    pedacos = []
    pos, n = 0, len(texto)
    while pos < n:
        fim = pos + _melhor_ponto_de_corte(texto[pos:pos + TAMANHO_MAXIMO_CHUNK], TAMANHO_MAXIMO_CHUNK)
        # Sobra curta demais não vira chunk próprio: é absorvida pelo pedaço
        # atual, que pode passar do teto em até TAMANHO_MINIMO_CHUNK.
        if n - fim < TAMANHO_MINIMO_CHUNK:
            fim = n
        pedaco = texto[pos:fim].strip()
        if pedaco:
            pedacos.append(pedaco)
        if fim >= n:
            break
        # Sobrepõe, mas sempre avança pelo menos 1 caractere — garante
        # progresso mesmo se SOBREPOSICAO_CHUNK for maior que o corte.
        pos = max(fim - SOBREPOSICAO_CHUNK, pos + 1)

    return pedacos


def dividir_em_chunks(texto) -> List[Chunk]:
    """Fatia o texto em chunks preservando o caminho hierárquico dos headings.

    Cada heading (`#` a `######`) empilha contexto: um chunk gerado sob
    "## EPIs" dentro de "# Segurança" carrega `caminho_heading="Segurança > EPIs"`,
    mesmo quando a seção é grande e vira vários chunks — nenhum pedaço fica
    órfão do título ao qual pertence.

    Chunks consecutivos de uma seção grande recebem `SOBREPOSICAO_CHUNK`
    caracteres de sobreposição, pra não perder contexto na fronteira do corte.
    Sobra menor que `TAMANHO_MINIMO_CHUNK` é absorvida pelo pedaço anterior.

    Texto antes do primeiro heading vira chunk(s) com `caminho_heading=None`.
    Documento vazio devolve [].
    """
    if not texto or not texto.strip():
        return []

    secoes = []  # (caminho_heading, linhas_da_secao)
    pilha, atual, caminho_atual = [], [], None

    for linha in texto.splitlines():
        m = _RE_HEADING.match(linha)
        if m:
            if atual:
                secoes.append((caminho_atual, atual))
                atual = []
            nivel, titulo = len(m.group(1)), m.group(2).strip()
            pilha = _atualizar_pilha_headings(pilha, nivel, titulo)
            caminho_atual = _caminho_heading(pilha)
        atual.append(linha)
    if atual:
        secoes.append((caminho_atual, atual))

    chunks = []
    for caminho, linhas_secao in secoes:
        for pedaco in _dividir_secao('\n'.join(linhas_secao)):
            chunks.append(Chunk(texto=pedaco, caminho_heading=caminho, indice=len(chunks)))

    return chunks


# Ollama sobe no compose com OLLAMA_HOST; fora dele, localhost resolve.
OLLAMA_URL = config('OLLAMA_HOST', default='http://localhost:11434')
# Modelo de embedding: trocável por .env sem tocar no código (decisão da daily).
MODELO_EMBEDDING = config('OLLAMA_EMBEDDING_MODEL', default='nomic-embed-text')
# Inferência local é lenta: timeout generoso para lotes grandes.
TEMPO_LIMITE_EMBEDDINGS = 120


class FalhaDeEmbeddingError(Exception):
    """Ollama fora do ar, modelo não baixado ou resposta inválida."""


def gerar_embeddings(textos):
    """Gera embeddings de todos os textos em uma única chamada ao Ollama.

    Recebe lista de textos (use `texto_para_embedding` dos chunks) e devolve
    lista de vetores na mesma ordem. Lista vazia devolve [] sem chamar o serviço.
    """
    if not textos:
        return []

    try:
        resposta = requests.post(
            f'{OLLAMA_URL}/api/embed',
            json={'model': MODELO_EMBEDDING, 'input': textos},
            timeout=TEMPO_LIMITE_EMBEDDINGS,
        )
        resposta.raise_for_status()
        return resposta.json()['embeddings']
    except (requests.RequestException, KeyError) as erro:
        raise FalhaDeEmbeddingError(
            f'Serviço de embeddings indisponível em {OLLAMA_URL}: {erro}'
        ) from erro

def indexar_documento(documento):
    """Pipeline completo: extrair → fatiar → vetorizar → gravar em lote.

    Recebe a instância de Documento (a extração usa o caminho do arquivo no
    storage e a gravação usa as FKs documento/projeto); devolve a quantidade
    de chunks gravados. Documento sem conteúdo devolve 0 sem chamar Ollama
    nem banco. As exceções nomeadas da extração e dos embeddings sobem para
    a #4-4 marcar o estado de erro.
    """
    texto = extrair_texto(documento.arquivo.name)
    chunks = dividir_em_chunks(texto)
    if not chunks:
        return 0

    vetores = gerar_embeddings([c.texto_para_embedding for c in chunks])
    if len(vetores) != len(chunks):
        raise FalhaDeEmbeddingError(
            f'Ollama devolveu {len(vetores)} vetores para {len(chunks)} chunks.'
        )

    registros = [
        ChunkDoc(
            # `conteudo` recebe o texto já com o caminho do heading: o modelo
            # ainda não tem campos separados para isso (pedido à mavy).
            conteudo=c.texto_para_embedding,
            embedding=vetor,
            documento=documento,
            projeto=documento.projeto,
        )
        for c, vetor in zip(chunks, vetores)
    ]
    ChunkDoc.objects.bulk_create(registros)
    return len(registros)