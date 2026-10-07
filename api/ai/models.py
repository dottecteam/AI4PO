from django.db import models
# Importamos os campos específicos de vetor e o índice HNSW do pgvector
from pgvector.django import VectorField, HnswIndex
from projects.models import Projeto, Documento
from django.conf import settings

# Entidade "ChunkDoc" do diagrama: trechos fatiados do documento para a IA
class ChunkDoc(models.Model):
    # Relação 'dividido em': o trecho pertence a um documento específico
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='chunks')
    # #IdProjeto no diagrama: referência direta ao projeto para agilizar filtros
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='chunks')
    conteudo = models.TextField()

    # Campo vetorial que armazena o embedding. As dimensões precisam bater com o modelo
    # de embedding configurado em OLLAMA_EMBEDDING_MODEL (nomic-embed-text gera 768);
    # se divergir, o Postgres rejeita a gravação com "expected N dimensions".
    embedding = VectorField(dimensions=768)

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

class Conversa(models.Model):
    usuario_po = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversas"
    )
    projeto = models.ForeignKey(
        Projeto, null=True, blank=True, on_delete=models.SET_NULL, related_name="conversas"
    )
    titulo = models.CharField(max_length=120, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)  # toca sozinho a cada .save()

    class Meta:
        ordering = ["-atualizado_em"]  # mais recente primeiro, pra sidebar

    def __str__(self):
        return self.titulo or f"Conversa {self.pk}"


class MensagemChat(models.Model):
    PAPEL_CHOICES = [("user", "user"), ("assistant", "assistant")]

    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name="mensagens")
    papel = models.CharField(max_length=10, choices=PAPEL_CHOICES)
    conteudo = models.TextField()
    anexo_nome = models.CharField(max_length=255, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]  # ordem cronológica dentro da conversa
        indexes = [models.Index(fields=["conversa", "-id"])]

    def __str__(self):
        return f"{self.papel} @ conversa {self.conversa_id}"