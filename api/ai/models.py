from django.db import models
from pgvector.django import VectorField
from pgvector.django import VectorExtension, VectorField

class ChunkIndexado(models.Model):
    """Chunk vetorizado de um documento, pronto para busca semântica."""

    # Dimensões do vetor: casadas com o modelo de embedding do .env
    # (nomic-embed-text gera 768). Se a daily trocar o modelo, troca aqui.
    DIMENSOES_EMBEDDING = 768

    texto = models.TextField()
    caminho_heading = models.CharField(max_length=255, null=True, blank=True)
    indice = models.PositiveIntegerField()
    embedding = VectorField(dimensions=DIMENSOES_EMBEDDING)
    documento_caminho = models.CharField(max_length=255)
    # Texto por enquanto: vira ForeignKey quando a #2-1 criar a entidade Projeto.
    projeto = models.CharField(max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['documento_caminho', 'indice']