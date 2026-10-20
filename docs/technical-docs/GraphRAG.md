# GraphRAG — por que, como funciona e como rodar

Resumo do módulo para quem vai usar ou operar. O detalhe de implementação está em
`GraphRAG-pipeline-e-retrieval.md`; a discussão banco vetorial × banco de grafo está
em `Justificativa-banco-vetorial.md`.

## Por que escolhemos GraphRAG

A busca por similaridade responde **"o que está escrito nos documentos"**. Ela não
responde perguntas de relacionamento: *quem fez o frontend*, *o que depende do que*,
*o que foi decidido em qual sprint*, *quais temas formam um mesmo bloco*. Para isso
é preciso saber como as coisas se ligam, e similaridade de vetor não expressa ligação.

Decidimos **extrair um grafo tipado dos mesmos chunks já indexados** e guardar esse
grafo no PostgreSQL que o sistema já usa.

O que ficou de fora, e por quê:

- **Neo4j** — exigiria uma JVM e uma segunda fonte de verdade ao lado do Postgres.
  No hardware de desenvolvimento (16 GB de RAM compartilhados com Docker e Ollama) o
  custo de memória e de operação não se paga na escala atual.
- **Biblioteca de grafo como serviço** (Lettria e afins) — mandaria documento de
  cliente para um terceiro.
- **RAPTOR** — foi implementado e revertido: resolve resumo hierárquico, não
  relacionamento entre entidades.
- **Modelo pequeno na extração** — `llama3.2:3b` é ~2× mais rápido, mas superproduz
  arestas e classifica errado (marcou "sprint" como `pessoa`). `gemma2:9b` e
  `qwen2.5-coder:14b` apertam a memória; `qwen3.5:4b` devolve resposta vazia.
  Ficamos com **`qwen2.5:7b` sem persona**, que é o que segue JSON com disciplina.

## Como funciona

```
chunks do documento → LLM (JSON Schema) → validação determinística → Postgres
                                                                    ↘ comunidades (Louvain)
pergunta no chat → ferramenta do grafo → contexto de 1 salto → resposta
```

1. **Extração.** Cada lote de chunks vai para o modelo com um prompt que fixa as
   taxonomias (`pessoa`, `decisao`, `requisito`, `sprint`, `sistema`, `artefato`,
   `indicador`, `conceito` / `depende_de`, `implementa`, `decidido_em`,
   `pertence_a`, `resolve`, `bloqueia`, `deriva_de`, `menciona`) e um exemplo de
   saída. O `format` da API do Ollama recebe um **JSON Schema**, então chave
   obrigatória faltando e tipo inventado deixam de ser possíveis.
2. **Validação em Python.** O schema garante a forma; o conteúdo é checado no
   código: datas, caminhos, verbos e termos genéricos não viram nó; a chave de
   identidade (sem acento, pontuação, partículas nem espaços) faz `kayanmatta` e
   `Kayan da Matta` serem o mesmo nó.
3. **Gravação.** `Entidade`, `Relacao` e `Comunidade`, com as evidências ligando cada
   aresta aos trechos que a sustentam. Reingestir não duplica e nunca piora o que já
   existe (confiança e tipo só sobem, descrição só entra onde está vazia).
4. **Comunidades.** Louvain sobre as arestas acima da confiança mínima, com hubs e
   grupos pequenos tratados; título e resumo vêm do modelo.
5. **Retrieval.** No chat, `consultar_grafo_conhecimento` acha os nós da pergunta,
   expande um salto e devolve relações, descrições, temas e documentos de origem.
   **Sem chamada de LLM no caminho.**

Tudo é **por projeto**: não há grafo global, e nenhuma consulta roda sem
`projeto_id`.

## Como rodar

Pré-requisitos: banco no Docker e Ollama com a GPU integrada ligada.

```powershell
docker compose up -d db
$env:OLLAMA_IGPU_ENABLE = "1"; ollama serve
```

Depois de enviar e indexar os documentos pela interface, a camada de grafo é
gerada por comando:

```bash
# extrai entidades e relações de um projeto (3 chunks por chamada ao modelo)
docker compose run --rm backend python manage.py graphrag_ingest --projeto 6 --lote 3

# agrupa em comunidades e gera os resumos
docker compose run --rm backend python manage.py graphrag_comunidades --projeto 6

# imagem do grafo (global + um painel por comunidade)
docker compose run --rm backend python manage.py graphrag_draw --out /app/grafico.png
```

Use `--completo` sempre que **mudar o prompt, a taxonomia ou os filtros**: a
ingestão normal só lê chunks ainda não processados, então a mudança não se aplica
retroativamente ao que já foi gravado.

Variáveis que importam (no `.env`):

| variável | para quê |
|---|---|
| `GRAPH_MODEL` | modelo de extração; hoje `qwen2.5:7b` |
| `GRAPH_CONF_MIN` | corte de confiança (0.5) usado por desenho, comunidades e retrieval |
| `OLLAMA_CHAT_TIMEOUT` | teto de cada chamada; saída longa chega a 150–230 s |
| `OLLAMA_KEEP_ALIVE` | mantém o modelo residente na GPU entre lotes |

## Tempo que custa

Medido neste notebook (Intel Core Ultra, iGPU Arc 140V, modelo 7B):

| operação | tempo |
|---|---|
| ingestão do AI4PO (31 trechos) | ~22 min |
| ingestão do RealIT (46 trechos) | ~24,5 min |
| geração de comunidades | ~40 s |
| retrieval no grafo, por pergunta | **~0,14 s** |

A ingestão é offline e roda uma vez por projeto — o que o usuário sente é o
retrieval, que não chama o modelo. O que faz o tempo de ingestão variar é o teto de
extração por lote (mais entidades por chamada = grafo mais rico e ingestão ~2× mais
longa) e o `keep_alive` do Ollama: se o modelo sai da GPU entre lotes, cada chamada
paga o carregamento de novo.
