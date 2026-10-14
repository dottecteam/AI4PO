# Definição do limite de similaridade para alertas de requisitos

## Decisão

Para a primeira versão da feature #7, o alerta deve considerar um requisito
como potencialmente semelhante quando:

- **similaridade de cosseno ≥ 0,81**; ou, de forma equivalente,
- **distância de cosseno ≤ 0,19**.

O valor foi calibrado com requisitos reais e literais dos backlogs do AI4PO,
usando o mesmo modelo de embeddings adotado pelo sistema. No conjunto avaliado,
o corte obteve precisão de **88,9%**, recall de **80,0%** e F1 de **84,2%**.

Um limiar isolado ainda não compreende a intenção do requisito. Portanto, o
resultado deve ser apresentado como **“possível requisito semelhante”**, e não
como confirmação automática de duplicidade.

## Contexto técnico

O backend gera embeddings pelo endpoint `/api/embed` do Ollama, com o modelo
`nomic-embed-text` configurado por `OLLAMA_EMBEDDING_MODEL`. O modelo produz
vetores de **768 dimensões**, valor usado pelo `VectorField` em
`api/ai/models.py`.

O PostgreSQL usa pgvector e um índice HNSW com `vector_cosine_ops`. Na consulta
Django, `CosineDistance` devolve a distância de cosseno:

```text
distância de cosseno = 1 - similaridade de cosseno
```

Assim, `similaridade ≥ 0,81` e `distância ≤ 0,19` representam a mesma regra.

## Metodologia

O benchmark foi executado em 13 de outubro de 2026 com:

- Ollama 0.34.2;
- `nomic-embed-text:latest`, identificador `0a109f422b47`;
- vetores de 768 dimensões;
- textos em português;
- 30 pares rotulados e 29 textos únicos;
- uma única chamada em lote ao endpoint `/api/embed`.

Os textos não são paráfrases criadas para o benchmark. Cada um é uma transcrição
do conteúdo de uma User Story já versionada em um destes documentos:

- [`product-backlog.md`](../scrum/product-backlog.md);
- [`sprint-1-backlog.md`](../scrum/sprint-backlog/sprint-1-backlog.md);
- [`sprint-2-backlog.md`](../scrum/sprint-backlog/sprint-2-backlog.md);
- [`sprint-3-backlog.md`](../scrum/sprint-backlog/sprint-3-backlog.md).

Cada par registra `source_a` e `source_b`, com arquivo e ID do requisito de
origem. Os testes automatizados verificam que os textos continuam presentes
nesses arquivos. Isso impede que um requisito alterado deixe de ser rastreável
sem que o benchmark acuse a divergência.

O conjunto foi dividido igualmente:

| Grupo | Quantidade | Critério de rotulagem | Resultado esperado |
| --- | ---: | --- | --- |
| Requisitos equivalentes | 10 | A mesma necessidade aparece em versões reais do Product Backlog e do Sprint Backlog | Exibir alerta |
| Mesmo domínio, intenção diferente | 10 | Os requisitos compartilham assunto ou vocabulário, mas pedem ações diferentes | Não exibir alerta |
| Requisitos distintos | 10 | Os requisitos tratam de funcionalidades diferentes | Não exibir alerta |

O dataset completo está em
[`scripts/similarity_pairs.json`](../../scripts/similarity_pairs.json). O script
calcula a similaridade de cosseno, avalia a matriz de confusão para cada score
observado e escolhe o melhor F1. Em caso de empate, prioriza menos falsos
positivos, maior precisão, maior recall e maior corte.

O melhor corte medido foi `0,810202`. O valor operacional ficou em **0,81**,
pois essa redução para duas casas decimais preserva exatamente a matriz de
confusão do corte medido. Arredondar sempre para cima até `0,82` não eliminaria
o falso positivo restante e transformaria dois verdadeiros positivos em falsos
negativos; por isso esse arredondamento foi descartado.

## Resultados

### Distribuição por grupo

| Grupo | Mínimo | Média | Máximo |
| --- | ---: | ---: | ---: |
| Requisitos equivalentes | 0,742518 | 0,839404 | 0,908972 |
| Mesmo domínio, intenção diferente | 0,644847 | 0,726225 | 0,853015 |
| Requisitos distintos | 0,600346 | 0,642123 | 0,685089 |

Existe sobreposição entre requisitos equivalentes e requisitos relacionados ao
mesmo domínio. Isso confirma que palavras e estruturas compartilhadas podem
dominar o embedding mesmo quando a ação solicitada é diferente.

### Comparação de pontos de corte

| Similaridade mínima | VP | FP | VN | FN | Precisão | Recall | F1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0,55 | 10 | 20 | 0 | 0 | 0,333 | 1,000 | 0,500 |
| 0,60 | 10 | 20 | 0 | 0 | 0,333 | 1,000 | 0,500 |
| 0,65 | 10 | 12 | 8 | 0 | 0,455 | 1,000 | 0,625 |
| 0,70 | 10 | 5 | 15 | 0 | 0,667 | 1,000 | 0,800 |
| 0,75 | 9 | 4 | 16 | 1 | 0,692 | 0,900 | 0,783 |
| 0,80 | 8 | 2 | 18 | 2 | 0,800 | 0,800 | 0,800 |
| **0,81** | **8** | **1** | **19** | **2** | **0,889** | **0,800** | **0,842** |
| 0,85 | 5 | 1 | 19 | 5 | 0,833 | 0,500 | 0,625 |
| 0,90 | 1 | 0 | 20 | 9 | 1,000 | 0,100 | 0,182 |

No corte escolhido, a matriz de confusão foi:

- 8 verdadeiros positivos;
- 1 falso positivo;
- 19 verdadeiros negativos;
- 2 falsos negativos.

Os resultados completos, incluindo origens, textos, score, distância e
classificação de cada par, estão em
[`resultados-benchmark-similaridade.csv`](resultados-benchmark-similaridade.csv).

### Casos que delimitam a decisão

O único falso positivo no corte `0,81` foi:

- conversar com o Chatbot versus exibir as fontes usadas pelo Chatbot:
  `0,853015` (`borderline-03`).

Os falsos negativos foram:

- sugerir documentos relacionados em duas versões reais do requisito:
  `0,752756` (`equivalent-09`);
- analisar uma especificação e identificar lacunas em duas versões reais do
  requisito: `0,742518` (`equivalent-06`).

Esses casos justificam a linguagem de incerteza na interface. Também mostram
por que elevar o corte não resolve sozinho a ambiguidade: em `0,85`, o mesmo
falso positivo permanece, enquanto metade dos requisitos equivalentes deixa de
ser encontrada.

## Diretriz para a task #7-2

Centralizar o valor em configuração, usando nomes que deixem explícita a
métrica:

```python
SIMILARITY_THRESHOLD = 0.81
MAX_COSINE_DISTANCE = 1.0 - SIMILARITY_THRESHOLD  # 0.19
```

Exemplo de consulta com Django e pgvector:

```python
from pgvector.django import CosineDistance

MAX_COSINE_DISTANCE = 0.19

similares = (
    ChunkDoc.objects
    .annotate(distance=CosineDistance("embedding", vetor_requisito))
    .filter(distance__lte=MAX_COSINE_DISTANCE)
    .order_by("distance")
)
```

Ao montar a resposta da API, a similaridade pode ser apresentada como
`1.0 - distance`. A implementação deve manter:

- o operador inclusivo (`>= 0,81` ou `<= 0,19`);
- o mesmo modelo de embedding na indexação e na consulta;
- ordenação por menor distância;
- origem do resultado, com projeto e documento;
- linguagem de possibilidade, sem afirmar automaticamente que existe uma
  duplicidade.

O benchmark conclui a calibração exigida pela task #7-1. A task #7-2 deverá
validar a integração com `ChunkDoc`, porque a indexação armazena trechos de até
aproximadamente 1.000 caracteres e pode acrescentar o caminho de headings em
`Chunk.texto_para_embedding`. Essa diferença de representação é uma condição
para acompanhar e eventualmente recalibrar, mas não altera a evidência de
requisitos reais usada nesta decisão.

Se o modelo, a dimensão, os prefixos de tarefa ou o pré-processamento forem
alterados, os documentos devem ser reindexados e este benchmark deve ser
executado novamente antes de reutilizar `0,81`.

## Diretrizes para interface e testes

A interface deve usar uma mensagem como **“Encontramos um possível requisito
semelhante”**. Não deve afirmar automaticamente que o requisito é duplicado.

Na task #7-4, os testes de integração devem cobrir pelo menos:

1. similaridade exatamente igual a `0,81`: alerta exibido;
2. similaridade logo abaixo de `0,81`: alerta não exibido;
3. distância exatamente igual a `0,19`: resultado incluído;
4. ordenação dos resultados da menor para a maior distância;
5. retorno da origem do requisito semelhante;
6. ausência de alerta quando não houver candidato dentro do limite.

## Reprodução do benchmark

Com o Ollama ativo e o modelo instalado:

```powershell
ollama pull nomic-embed-text
python scripts/benchmark_similarity.py
```

O comando lê [`scripts/similarity_pairs.json`](../../scripts/similarity_pairs.json)
e regenera `resultados-benchmark-similaridade.csv`. O script depende apenas da
biblioteca padrão do Python.

Os testes unitários do cálculo, do arredondamento, da rastreabilidade do dataset
e da geração do CSV podem ser executados com:

```powershell
python -m unittest scripts.test_benchmark_similarity -v
```

## Limitações e próxima calibração

Os 30 pares são requisitos reais do AI4PO, mas ainda formam uma amostra pequena
e pertencem a um único produto. Além disso, a equivalência foi rotulada para
este benchmark; antes de uma calibração de produção, pelo menos duas pessoas
devem revisar independentemente os rótulos e registrar divergências.

Quando houver requisitos históricos da empresa já indexados, recomenda-se
ampliar o dataset com esses exemplos. Se a sobreposição permanecer, a busca
vetorial deve ser tratada como recuperação de candidatos e combinada com uma
segunda etapa de classificação de intenção, em vez de tentar eliminar a
ambiguidade apenas aumentando o limiar.
