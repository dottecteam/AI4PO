# Estratégia de Indexação do AI4PO

## Contexto

A task #4-3 implementa o pipeline de indexação de documentos do AI4PO,
fechando a cadeia de dependências da story #4:

- #3-1 (formatos aceitos) → #4-2 (extração de texto) → #4-3 (chunking + embeddings + armazenamento).

A DoD exige que documentos enviados sejam convertidos em chunks vetorizados
e armazenados na base vetorial.

## Arquitetura

O pipeline é composto por quatro estágios soltos, cada um com testes próprios:

1. **Extração** (`ai.extraction`): converte arquivos `.md`/`.txt` do storage
   em texto UTF-8, preservando headings para o chunking.
2. **Chunking** (`ai.indexing.dividir_em_chunks`): fatia o texto em pedaços
   coerentes, com caminho hierárquico de headings, sobreposição de fronteira
   e absorção de sobra.
3. **Embeddings** (`ai.indexing.gerar_embeddings`): gera vetores em batch
   via Ollama local (endpoint `/api/embed`).
4. **Armazenamento** (`ai.indexing.indexar_documento`): orquestra os três
   estágios e grava em lote no modelo `ChunkDoc` (pgvector), usando as FKs
   `documento` e `projeto` da instância recebida.

## Chunking

Constantes e justificativas:

- `TAMANHO_MAXIMO_CHUNK = 1000`: equilíbrio entre contexto rico e precisão
  de busca.
- `SOBREPOSICAO_CHUNK = 150`: fronteira repetida entre chunks vizinhos,
  evitando perda de informação no corte.
- `TAMANHO_MINIMO_CHUNK = 80`: sobra menor que isso é absorvida pelo chunk
  anterior, evitando ruído na base.

O chunking preserva o caminho hierárquico dos headings (ex.: "Segurança >
EPIs > Capacete"), permitindo desambiguar trechos de conteúdo parecido.

## Embeddings

- Modelo proposto: `nomic-embed-text` (768 dimensões), configurável via
  variável de ambiente `OLLAMA_EMBEDDING_MODEL`.
- Chamada batch: uma requisição HTTP para N textos, preservando a ordem.
- Timeout de 120s para inferência local.
- Exceção nomeada `FalhaDeEmbeddingError` para falhas de conexão ou
  resposta inválida.

## Armazenamento

O modelo `ChunkDoc` (`ai.models`, vindo da modelagem da feature de banco)
armazena cada chunk com:

- `documento` (FK → `projects.Documento`, `CASCADE`, `related_name='chunks'`);
- `projeto` (FK → `projects.Projeto`, `CASCADE`);
- `conteudo` (TextField): recebe o texto do chunk **já com o caminho de
  heading prefixado**, porque o modelo não tem campo separado para isso;
- `embedding` (`VectorField`, declarado com 1536 dimensões);
- índice `chunk_vector_cosine_idx` (`HnswIndex`, `m=16`,
  `ef_construction=64`, `vector_cosine_ops`).

Cadeia de migrations do app `ai`: `0001_enable_pgvector` (`VectorExtension`),
`0002_initial` (tabela) e `0003_initial` (FKs + índice HNSW). A cadeia foi
aplicada com sucesso no Postgres do `docker-compose.yml`.

### Pendências registradas com a autora do modelo

- **Dimensão do vetor**: a coluna exige 1536, mas o `nomic-embed-text` devolve
  768. Provado por gravação real no Postgres:
  `DataError: expected 1536 dimensions, not 768`. Os testes não capturam isso
  porque o Ollama é mockado. A correção (dimensão 768, ou troca do modelo de
  embeddings) é mudança em `ai.models`, de responsabilidade da mavygarcia.
- **Campos de rastreamento**: sem `caminho_heading`, `indice` e `criado_em`
  não dá para deduplicar reprocessamentos nem ordenar chunks na resposta do
  RAG; hoje tudo é achatado dentro de `conteudo`.

## Decisões

- **RAG clássico na Sprint 1**: GraphRAG ficou adiado como evolução
  (estudo comparativo com dados reais do time). O pipeline em estágios
  soltos permite inserir um estágio de grafo depois sem reescrever o que
  existe.
- **Modelo de chunk único**: a pipeline foi adaptada ao `ChunkDoc` já
  modelado pela feature de banco em vez de manter um modelo duplicado; a
  migration própria do app `ai` foi descartada para não haver duas
  `initial = True` concorrentes no mesmo app.
- **Testes agora exigem Postgres**: o `HnswIndex` gera
  `CREATE INDEX ... WITH (...)`, que o SQLite não entende. Os 21 testes de
  unidade rodam contra o banco de teste criado pelo runner, com
  `docker compose up -d db` de pé.

## Considerações futuras

O GraphRAG é candidato a evolução em Sprint futura, combinando busca
vetorial (pgvector) com Knowledge Graph (entidades e relações extraídas
dos documentos). O estudo está documentado em `AI4PO_GraphRAG.md` e
inclui:

- Extração de entidades/relações via LLM;
- Tabelas complementares `knowledge_entity` e `knowledge_relation`;
- Recuperação híbrida: embedding encontra o relevante, grafo expande
  pelas relações.

A migração para GraphRAG não substitui o RAG clássico; adiciona uma
camada complementar de conhecimento.

## Dependências

- `pgvector==0.4.2` (VectorField + VectorExtension para Django);
- `psycopg[binary]==3.2.13` (driver do Postgres);
- `requests==2.32.5` (chamada HTTP ao Ollama).