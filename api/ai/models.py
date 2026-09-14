from django.db import models
# Importamos os campos específicos de vetor e o índice HNSW do pgvector
from pgvector.django import VectorField, HnswIndex
from projects.models import Projeto, Documento

# Entidade "ChunkDoc" do diagrama: trechos fatiados do documento para a IA
class ChunkDoc(models.Model):
    # Relação 'dividido em': o trecho pertence a um documento específico
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='chunks')
    # #IdProjeto no diagrama: referência direta ao projeto para agilizar filtros
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='chunks')
    conteudo = models.TextField()
    
    # Campo vetorial que armazena o embedding (1536 dimensões é o tamanho padrão dos modelos de IA)
    embedding = VectorField(dimensions=1536)

    class Meta:
        indexes = [
            # Índice HNSW para acelerar drasticamente a busca por similaridade de cosseno
            HnswIndex(
                name='chunk_vector_cosine_idx',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops']
            )
        ]

    def __str__(self):
        return f"Chunk {self.id} - Doc {self.documento_id}"
    