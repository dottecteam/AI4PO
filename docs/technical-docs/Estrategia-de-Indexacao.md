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
   estágios e grava em lote no modelo `ChunkIndexado` (pgvector).

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

O modelo `ChunkIndexado` (ai.models) armazena cada chunk com:

- `texto`, `caminho_heading`, `indice` (do chunking);
- `embedding` (VectorField do pgvector, 768 dimensões);
- `documento_caminho`, `projeto` (metadados para filtragem e reprocessamento);
- `criado_em` (auditoria).

A migration inclui `VectorExtension()` para criar a extensão `vector` no
Postgres antes da tabela. O campo `projeto` é CharField (texto) por
enquanto; virará ForeignKey quando a entidade Projeto (#2-1) existir.

## Decisões

- **RAG clássico na Sprint 1**: GraphRAG ficou adiado como evolução
  (estudo comparativo com dados reais do time). O pipeline em estágios
  soltos permite inserir um estágio de grafo depois sem reescrever o que
  existe.
- **CharField em `projeto`**: evita acoplamento com a #2-1; metadado
  simples primeiro, FK quando a entidade existir.
- **Testes em SQLite**: os testes atuais são de unidade (chunking é texto
  puro, embeddings usam mock, VectorExtension é ignorada em SQLite). A
  validação de integração (migrate + gravação + busca vetorial real)
  depende da virada do `DATABASES` para Postgres.

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