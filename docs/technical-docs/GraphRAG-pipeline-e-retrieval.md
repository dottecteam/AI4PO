# GraphRAG — arquitetura, pipeline e retrieval

Módulo: `api/ai/graphrag.py` (app `ai`). Feature #13, equipe DotTec.
Data de referência: 20/10/2026.

## O que é e por que existe

O RAG vetorial clássico responde "o que está escrito nos documentos". Ele não
responde perguntas de **relacionamento**: quem fez qual componente, o que depende
de quê, o que foi decidido em qual sprint, quais temas pertencem ao mesmo grupo.
O GraphRAG acrescenta essa camada: extrai um grafo tipado dos mesmos chunks já
indexados e usa esse grafo para montar contexto multi-salto.

O grafo vive no **PostgreSQL existente**, sem Neo4j. `Entidade`, `Relacao` e
`Comunidade` são tabelas Django; as evidências são uma relação N:N com
`ChunkDoc`. A decisão e o custo de migrar para um banco de grafo estão em
`Justificativa-banco-vetorial.md`.

## Modelos

| modelo | papel | campos que importam |
|---|---|---|
| `Entidade` | nó do grafo | `chave` (identidade normalizada), `tipo` (taxonomia fechada), `descricao`, `projeto` |
| `Relacao` | aresta tipada | `origem`, `destino`, `tipo`, `confianca`, `projeto`; unicidade pela tripla `(origem, destino, tipo)` |
| `Relacao.evidencias` | rastreabilidade | N:N com `ChunkDoc`: quais trechos sustentam a aresta |
| `Comunidade` | grupo temático | `titulo`, `resumo` (gerado pelo LLM), `tamanho`, membros N:N |
| `ChunkDoc.grafo_processado` | indexação incremental | evita reler o mesmo trecho a cada rodada |

Todo o grafo é **por projeto**: `projeto` é filtro em criação, detecção de
comunidades e retrieval. Não existe um grafo global misturando clientes.

## Pipeline de ingestão

```
ChunkDoc (>=150 caracteres) → lote de N chunks → LLM (JSON Schema) → validação
determinística → Entidade/Relacao/evidências → marca chunk como processado
```

**Prompt.** Enviado como `system`; o texto do lote vai como `user`. Pede um objeto
com `entidades` e `relacoes`, lista as duas taxonomias permitidas e traz um exemplo
few-shot. O exemplo não é decorativo: sem ele o modelo devolvia entidades com
`descricao` vazia (medido: 0/7 preenchidas sem exemplo, 9/9 com exemplo).

**JSON Schema nativo.** `_chat(formato="json_schema")` envia um schema ao Ollama, que
restringe a decodificação: chave obrigatória ausente e `tipo` fora do `enum` deixam
de ser possíveis. Detalhe importante: `minLength`/`maxLength` **não** devem ser usados
— com essa restrição a mesma extração caiu de 30 s para 193 s e devolveu JSON
truncado no Qwen 2.5 7B.

**Validação determinística** (o schema só garante forma; conteúdo é checado aqui):

- `_eh_lixo` rejeita data, caminho/breadcrumb, arquivo de configuração, verbo
  conjugado, sigla curta, frase longa (mais de 6 palavras) e substantivo genérico.
- `_chave_identidade` normaliza para minúsculo, sem acento, sem pontuação, sem
  artigos/partículas e **sem espaços**. É o que faz `kayanmatta` e
  `Kayan da Matta` virarem o mesmo nó, sem dicionário de apelidos.
- Tipo de entidade fora da lista vira `conceito`; tipo de aresta fora da lista vira
  `menciona`. Sem esta última, o banco acumulou 9 tipos inventados (`coleta`,
  `processa`, `decide`, `versionado`…).
- `confianca` é convertida e limitada a `[0, 1]`.

**Idempotência e transação.** Reingestir o mesmo trecho não duplica: entidade
reaproveitada pela `chave`, aresta por `get_or_create` na tripla. Um lote inteiro é
um `transaction.atomic()`, então não fica entidade sem relação nem relação sem
evidência. Enriquecimento é **monotônico**: confiança só sobe, descrição só entra
onde ainda está vazia, e o tipo `conceito` (dado a quem nasceu só como ponta de
relação) cede lugar ao tipo declarado pelo modelo.

**Incremental.** Por padrão só chunks com `grafo_processado=False`. Use
`--completo` depois de mudar prompt, filtro ou taxonomia — a mudança não se aplica
retroativamente ao que já foi gravado.

## Detecção de comunidades

NetworkX + Louvain, com `confianca` como peso das arestas e `seed` fixa para
reprodutibilidade. Três regras que importam:

- só entram arestas com `confianca >= GRAPH_CONF_MIN` (0.5), para chute fraco não
  colar temas distintos;
- **hubs ficam fora da detecção** (grau ≥ 2× a média): um nome de produto ligado a
  tudo fundiria o grafo inteiro numa comunidade só;
- grupos abaixo de `--min-tamanho` (4) são reencaixados na comunidade vizinha mais
  próxima, em vez de virar micro-comunidade sem sentido.

Título e resumo saem de uma chamada ao LLM com as entidades, tipos, descrições e
até 20 arestas internas. Se o Ollama cair, a partição vale e o resumo fica vazio.
Rodar de novo **regenera do zero** (apaga as comunidades do projeto antes).

## Retrieval no grafo (task #13-3)

`buscar_no_grafo(pergunta, projeto_id, max_entidades=5, max_saltos=1)` devolve texto
puro para o agente ler:

1. normaliza a pergunta com a **mesma** função usada na ingestão;
2. escolhe nós semente por termo inteiro (nome vale 2, descrição vale 1) e desempata
   por grau — comparação por token, não por substring, para `acao` não pescar
   `autenticacao`;
3. expande um salto pelas arestas acima da confiança mínima (é isso que responde
   "quem fez o frontend?" ligando pessoa → artefato);
4. anexa o resumo das comunidades envolvidas e os documentos de evidência.

Custo medido: **~143 ms**, sem nenhuma chamada de LLM no caminho — o retrieval está
na frente da resposta ao usuário.

Na view do chat, `consultar_grafo_conhecimento` é uma ferramenta do agente ao lado
de `buscar_contexto_projetos` (RAG vetorial). O modelo escolhe qual usar pela
descrição: perguntas de relacionamento vão para o grafo, conteúdo literal de
documento vai para a busca vetorial.

## Configuração

| variável | padrão | efeito |
|---|---|---|
| `GRAPH_MODEL` | `qwen2.5:7b` | modelo de extração; **sem persona** (o Modelfile do chat atrapalha JSON) |
| `OLLAMA_URL` | `http://localhost:11434` | dentro do container o compose injeta `host.docker.internal` |
| `OLLAMA_KEEP_ALIVE` | `30m` | mantém o modelo residente na GPU; sem isso cada lote paga cold-load |
| `OLLAMA_CHAT_TIMEOUT` | `300` | teto da chamada; saída longa com schema chega a 150–230 s |
| `GRAPH_CONF_MIN` | `0.5` | régua comum a desenho, comunidades e retrieval |

Hardware de referência: Intel Core Ultra 7 (Lunar Lake), iGPU Arc 140V via Vulkan,
16 GB compartilhados. O Ollama **não** usa a NPU; aceleração é GPU/CPU. Taxas
medidas: 10,9–17,4 tokens/s no 7B sob schema. `llama3.2:3b` é ~2× mais rápido e
também respeita o `enum`, mas inventa mais arestas. Modelos "thinking" (qwen3.5)
devolvem resposta vazia com `num_predict` curto: não usar para extração.

## Comandos

```bash
docker compose run --rm backend python manage.py graphrag_ingest --projeto 6 --lote 3
docker compose run --rm backend python manage.py graphrag_ingest --completo   # após mudar prompt/filtro
docker compose run --rm backend python manage.py graphrag_comunidades --projeto 6
docker compose run --rm backend python manage.py graphrag_draw --out /app/grafico.png
```

## Qualidade medida (rebuild completo com documentos reais)

Medido no RealIT (6 documentos, 46 trechos elegíveis), três estados do mesmo corpus:

| | pipeline antigo | teto 8/10 | teto 12/15 |
|---|---|---|---|
| entidades | 107 | 57 | 91 |
| com descrição | 3 (2,8%) | 57 (100%) | 91 (100%) |
| arestas | 224 | 91 | 121 |
| arestas com tipo inválido | 18 (9 tipos) | 0 | 0 |
| comunidades | 9 | 4 | 6 |
| tempo da ingestão | ~10,7 min | 11,4 min | 24,5 min |

O teto de extração por lote é o troco entre **limpeza** e **cobertura**: com 8/10 o
grafo ficou enxuto mas perdeu nós legítimos; com 12/15 ele recupera 52 dos nós que
já existiam no grafo antigo e acrescenta 39 novos, ao custo do dobro do tempo. Como
a ingestão é offline e roda uma vez por projeto, ficou 12/15.

Comparar grafos exige cuidado: a `chave` já é armazenada normalizada, então
normalizar de novo corrompe a comparação (um `s` final é cortado duas vezes) e a
diferença sai falsa.

No projeto AI4PO (4 documentos, 31 trechos elegíveis), com o mesmo teto 12/15:
**111 entidades, 106 relações, 11 comunidades, 100% das entidades com descrição,
zero arestas fora da taxonomia e zero arestas no fallback `menciona`**, em 22,4 min
de ingestão + ~1 min de comunidades. Com o teto antigo eram 102/96/9 e 5 arestas
`menciona`, em 13,5 min.

## Limitações conhecidas

- **O produto vira hub.** A regra do prompt diz para não criar arestas com o nome do
  projeto, mas o modelo desobedece: `AI4PO` e `RealIT` aparecem ligados a dezenas de
  nós. É por isso que ficam "sem comunidade" (o filtro de hubs os exclui da
  detecção). Fechar isso exige validação no código, não no prompt.
- **Sinônimos próximos não colapsam.** `frontend`, `frontend do AI4PO` e `interface
  web do AI4PO` são três nós. A chave de identidade só une variações ortográficas da
  mesma string, não conceitos equivalentes.
- **Handle ≠ nome real quando não há ponte.** `jopaul0` e `João Paulo` seguem
  separados: nenhuma normalização aproxima as duas strings, e o modelo só unificaria
  se as visse no mesmo trecho. Resolver isso pede um campo de alias na entidade.
- **`Entidade.embedding` não é preenchido** por ninguém. O retrieval atual é léxico;
  busca semântica de nós é trabalho futuro.
- **O retrieval depende de `projeto_id` na requisição.** O chat do frontend ainda não
  envia esse campo, então pela interface a ferramenta do grafo não é acionada.

## Testes

`api/ai/tests.py`: `IdentidadeDeNoTests`, `RetrievalNoGrafoTests`,
`FerramentaDoGrafoNaViewTests` e `IngestaoDoGrafoTests` — 26 testes que cobrem
canonização, filtros, taxonomia de arestas, confiança, idempotência, modo
incremental, regeneração de comunidades, montagem do contexto e a ligação
view → ferramenta. Todos rodam com o LLM encenado (`patch` em `_chat`), sem GPU.
