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
    # GraphRAG: chunk já processado pela ingestão do grafo (indexação incremental).
    grafo_processado = models.BooleanField(default=False)

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
    resumo = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)  # toca sozinho a cada .save()
    resumido_ate_id = models.PositiveBigIntegerField(default=0)
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
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["id"]  # ordem cronológica dentro da conversa
        indexes = [models.Index(fields=["conversa", "-id"])]

    def __str__(self):
        return f"{self.papel} @ conversa {self.conversa_id}"

# Camada GraphRAG: grafo tipado de conceitos extraídos dos chunks +
# comunidades detectadas por NetworkX. Alimentado pela ingestão (graphrag.py).

class Entidade(models.Model):
    """Conceito extraído de um chunk (decisão, sistema, tema, pessoa, requisito)."""
    # FK opcional: permite restringir o grafo a um projeto quando desejado.
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='entidades', null=True, blank=True)
    nome = models.CharField(max_length=255)
    # Chave canônica (minúscula, sem acento, singular): evita 'Sprint 1' vs 'Sprint #1'
    chave = models.CharField(max_length=255, blank=True, default='', db_index=True)
    tipo = models.CharField(max_length=50, blank=True, default='')
    descricao = models.TextField(blank=True, default='')
    # Vetor opcional: habilita busca semântica de nós, não só de chunks
    embedding = VectorField(dimensions=768, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class Relacao(models.Model):
    """Aresta tipada entre duas entidades: o que transforma a árvore em GRAFO."""
    origem = models.ForeignKey(Entidade, on_delete=models.CASCADE, related_name='relacoes_partindo')
    destino = models.ForeignKey(Entidade, on_delete=models.CASCADE, related_name='relacoes_chegando')
    tipo = models.CharField(max_length=50)  # depende_de|conflita_com|decidiu|referencia|deriva_de
    descricao = models.TextField(blank=True, default='')
    confianca = models.FloatField(default=0.5)
    # Evidências: de quais chunks a aresta saiu (rastreabilidade / "origem")
    evidencias = models.ManyToManyField(ChunkDoc, related_name='relacoes', blank=True)
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='relacoes', null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Evita arestas duplicadas entre o mesmo par com o mesmo tipo
        constraints = [
            models.UniqueConstraint(fields=['origem', 'destino', 'tipo'], name='uniq_relacao_tripla')
        ]

    def __str__(self):
        return f"{self.origem.nome} -[{self.tipo}]-> {self.destino.nome}"


class Comunidade(models.Model):
    """Grupo de entidades relacionadas + resumo gerado pela IA (busca global)."""
    titulo = models.CharField(max_length=255, blank=True, default='')
    resumo = models.TextField(blank=True, default='')
    tamanho = models.IntegerField(default=0)
    membros = models.ManyToManyField(Entidade, related_name='comunidades', blank=True)
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='comunidades', null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo or f"Comunidade {self.id}"


class ProgressoGrafo(models.Model):
    """Progresso da ingestão do GraphRAG de um documento.

    Alimenta a barra de % no frontend: o upload dispara a ingestão em
    background e o front consulta este registro via endpoint de status.
    """
    ESTADOS = (
        ('processando', 'Processando'),
        ('concluido', 'Concluído'),
        ('erro', 'Erro'),
    )
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='progressos_grafo')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='progressos_grafo')
    total_chunks = models.IntegerField(default=0)
    chunks_processados = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=ESTADOS, default='processando')
    erro = models.TextField(blank=True, default='')
    iniciado_em = models.DateTimeField(auto_now_add=True)
    finalizado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-iniciado_em']

    @property
    def percentual(self):
        if self.total_chunks <= 0:
            return 100 if self.status == 'concluido' else 0
        return min(100, round(self.chunks_processados * 100 / self.total_chunks))

    def __str__(self):
        return f"Grafo doc {self.documento_id}: {self.chunks_processados}/{self.total_chunks} ({self.status})"


class LayoutGrafo(models.Model):
    """Posições dos nós do grafo salvas pelo usuário (estilo Obsidian: fixa onde arrumou).

    Um registro por (usuário, escopo). `projeto` nulo = layout do grafo GLOBAL
    (todos os projetos juntos); com `projeto` = layout daquele projeto.
    `posicoes` é um JSON { "<entidade_id>": {"x": <num>, "y": <num> } }.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='layouts_grafo')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, null=True, blank=True, related_name='layouts_grafo')
    posicoes = models.JSONField(default=dict, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Layouts de grafo"

    def __str__(self):
        escopo = f"projeto {self.projeto_id}" if self.projeto_id else "global"
        return f"Layout {escopo} de {self.usuario_id} ({len(self.posicoes)} nós)"