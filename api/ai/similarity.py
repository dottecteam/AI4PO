from dataclasses import dataclass

from pgvector.django import CosineDistance

from ai.indexing import FalhaDeEmbeddingError, gerar_embeddings
from ai.models import ChunkDoc


SIMILARITY_THRESHOLD = 0.81
MAX_COSINE_DISTANCE = 0.19
MAX_SIMILAR_RESULTS = 5
MENSAGEM_POSSIVEL_SIMILARIDADE = (
    "Encontramos um possível requisito semelhante."
)


@dataclass(frozen=True)
class ResultadoSimilaridade:
    chunk_id: int
    conteudo: str
    similaridade: float
    projeto_id: int
    projeto_titulo: str
    documento_id: int
    documento_nome: str


"""Normaliza a entrada e gera exatamente um vetor para a consulta."""
def gerar_vetor_de_requisito(texto: object) -> list[float] | None:
    if not isinstance(texto, str) or not texto.strip():
        return None
    texto_normalizado = texto.strip()
    vetores = gerar_embeddings([texto_normalizado])
    if len(vetores) != 1 or vetores[0] is None:
        raise FalhaDeEmbeddingError(
        )

    return vetores[0]


"""Busca as possíveis correspondências do texto na base indexada."""
def verificar_similaridade(texto: object) -> list[ResultadoSimilaridade]:
    vetor = gerar_vetor_de_requisito(texto)
    if vetor is None:
        return []

    chunks = (
        ChunkDoc.objects
        .select_related("projeto", "documento")
        .annotate(distance=CosineDistance("embedding", vetor))
        .filter(distance__lte=MAX_COSINE_DISTANCE)
        .order_by("distance", "id")[:MAX_SIMILAR_RESULTS]
    )

    return [
        ResultadoSimilaridade(
            chunk_id=chunk.id,
            conteudo=chunk.conteudo,
            similaridade=1.0 - float(chunk.distance),
            projeto_id=chunk.projeto_id,
            projeto_titulo=chunk.projeto.titulo,
            documento_id=chunk.documento_id,
            documento_nome=chunk.documento.nome,
        )
        for chunk in chunks
    ]
