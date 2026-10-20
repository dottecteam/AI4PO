import logging
import re

import numpy as np
from decouple import config
from pgvector.django import CosineDistance

from ai.indexing import FalhaDeEmbeddingError, dividir_em_chunks, gerar_embeddings
from ai.models import ChunkDoc

logger = logging.getLogger(__name__)

# Quantos trechos a busca devolve por padrão.
RAG_TOP_K = config("RAG_TOP_K", default=4, cast=int)

# Distância de cosseno máxima aceita (0 = idêntico, 1 = sem relação).
# Trechos mais distantes que isso não entram: melhor devolver "nada encontrado"
# do que fundamentar a resposta em um trecho irrelevante. Ponto de partida:
# calibre olhando as distâncias que o log de busca imprime com dados reais.
RAG_DISTANCIA_MAXIMA = config("RAG_DISTANCIA_MAXIMA", default=0.7, cast=float)

# O indexador grava `conteudo` como "[Caminho > Do > Heading]\n<trecho>"
# (ver ChunkDoc.conteudo em indexing.py); aqui separamos as duas partes.
_RE_PREFIXO_SECAO = re.compile(r"^\[(.+?)\]\n")


def responder_com_documento(texto_doc, pergunta):
    # 'pergunta' aqui é a palavra-chave ou frase que a IA decidiu usar para filtrar o documento
    chunks = dividir_em_chunks(texto_doc)

    if not chunks:
        return "Aviso: O documento fornecido está vazio ou não contém texto legível."

    print(f"\n[DEBUG IN-MEMORY RAG] {len(chunks)} chunks gerados do documento anexado.")

    # Gera vetores do documento e do termo de busca
    vetores = np.array(gerar_embeddings([c.texto_para_embedding for c in chunks]))
    vetores_pergunta = gerar_embeddings([pergunta])

    if not vetores_pergunta:
        return "Erro: Falha ao gerar vetor de busca para analisar o documento."

    vetor_pergunta = np.array(vetores_pergunta[0])

    # Cálculo de similaridade de cosseno usando NumPy
    sims = vetores @ vetor_pergunta / (
        np.linalg.norm(vetores, axis=1) * np.linalg.norm(vetor_pergunta)
    )

    # Pega os 4 trechos mais relevantes (protegido caso o documento seja menor que 4 chunks)
    k = min(4, len(chunks))
    top_k = np.argsort(sims)[::-1][:k]

    # Retorna APENAS os dados brutos para o Ollama ler como ferramenta
    contexto = "\n---\n".join(chunks[i].texto_para_embedding for i in top_k)

    return f"Conteúdo relevante extraído do documento enviado pelo usuário:\n{contexto}"


# ==========================================
# BUSCA SEMÂNTICA NA BASE VETORIAL
# ==========================================
def _separar_secao(conteudo):
    """Devolve (caminho_heading | None, trecho) a partir do `conteudo` gravado."""
    m = _RE_PREFIXO_SECAO.match(conteudo)
    if not m:
        return None, conteudo
    return m.group(1), conteudo[m.end():]


def buscar_trechos(consulta, usuario, projeto_id=None, limite=None,
                   distancia_maxima=RAG_DISTANCIA_MAXIMA):
    """Busca semântica nos documentos indexados, devolvendo trechos COM origem.

    Só enxerga chunks de projetos do próprio `usuario` (Projeto.usuario_po), então
    um PO nunca recebe trecho de documento de outro PO. Se `projeto_id` for de outro
    usuário, o resultado é simplesmente vazio.

    `distancia_maxima=None` desliga o corte de relevância. Levanta
    FalhaDeEmbeddingError se o Ollama não gerar o vetor da consulta.

    Cada item: chunk_id, projeto_id, projeto, documento_id, documento,
    secao (caminho de headings ou None), trecho (sem o prefixo de heading) e
    similaridade (1 - distância de cosseno; quanto maior, mais parecido).
    """
    vetores = gerar_embeddings([consulta])
    if not vetores:
        raise FalhaDeEmbeddingError("O serviço de embeddings não devolveu vetor para a consulta.")

    query = (
        ChunkDoc.objects
        .filter(projeto__usuario_po=usuario)
        .select_related("projeto", "documento")
        .annotate(distancia=CosineDistance("embedding", vetores[0]))
        .order_by("distancia")
    )
    if projeto_id:
        query = query.filter(projeto_id=projeto_id)
    if distancia_maxima is not None:
        query = query.filter(distancia__lte=distancia_maxima)

    trechos = []
    for c in query[: limite or RAG_TOP_K]:
        secao, texto = _separar_secao(c.conteudo)
        trechos.append({
            "chunk_id": c.id,
            "projeto_id": c.projeto_id,
            "projeto": c.projeto.titulo,
            "documento_id": c.documento_id,
            "documento": c.documento.nome,
            "secao": secao,
            "trecho": texto,
            "similaridade": round(1 - float(c.distancia), 4),
        })

    logger.info(
        "[RAG] consulta=%r projeto=%s -> %d trecho(s), similaridades=%s",
        consulta, projeto_id, len(trechos), [t["similaridade"] for t in trechos],
    )
    return trechos


def _formatar_contexto(trechos):
    """Texto que a LLM lê: cada trecho precedido da sua origem, para ela poder citar."""
    blocos = []
    for i, t in enumerate(trechos, start=1):
        origem = f"Projeto: {t['projeto']} | Documento: {t['documento']}"
        if t["secao"]:
            origem += f" | Seção: {t['secao']}"
        blocos.append(f"[Fonte {i}] {origem}\n{t['trecho']}")
    return "\n---\n".join(blocos)


def responder_com_base_vetorial(pergunta, usuario, projeto_id=None, fontes=None):
    """Ferramenta `buscar_contexto_projetos`: devolve texto para a LLM ler.

    `usuario` é obrigatório: a busca é restrita aos projetos dele.
    `fontes` (opcional) é uma lista que recebe os trechos estruturados, para a
    view devolver ao front junto com a resposta.
    """
    # 'pergunta' é a palavra-chave gerada pela IA (ex.: "requisitos de pagamento")
    trechos = buscar_trechos(pergunta, usuario, projeto_id=projeto_id)

    if not trechos:
        return "Nenhum trecho relevante foi encontrado nos documentos para este termo."

    if fontes is not None:
        fontes.extend(trechos)

    return (
        "Trechos relevantes encontrados nos documentos (cite o projeto e o documento "
        f"de origem ao usar uma informação):\n{_formatar_contexto(trechos)}"
    )