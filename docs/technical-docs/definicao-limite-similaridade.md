# Definição do limite de similaridade para alertas de requisitos

## Decisão

Para a primeira versão da feature #7, o alerta deve considerar um requisito
como potencialmente semelhante quando:

- **similaridade de cosseno ≥ 0,66**; ou, de forma equivalente,
- **distância de cosseno ≤ 0,34**.

Esse é um limiar inicial, calibrado para a comparação direta entre frases de
requisitos com o modelo e o endpoint usados atualmente pelo AI4PO. Ele deve ser
revisto quando o modelo, o pré-processamento ou o conjunto de requisitos mudar.
Como a base atual armazena chunks que podem incluir headings, a task #7-2 deve
validar o corte contra uma amostra desses chunks antes de tratá-lo como
calibrado para a consulta ao `ChunkDoc`.

O benchmark também mostrou que **um limiar isolado não separa perfeitamente**
requisitos equivalentes de requisitos apenas relacionados ao mesmo domínio.
Por isso, o resultado deve ser apresentado como "possível requisito
semelhante", e não como confirmação de duplicidade.

## Contexto técnico

O backend gera embeddings pelo endpoint `/api/embed` do Ollama, com o modelo
`nomic-embed-text` configurado por `OLLAMA_EMBEDDING_MODEL`. O modelo produz
vetores de **768 dimensões**, valor usado pelo `VectorField` em
`api/ai/models.py`. Na indexação existente, o texto pode ser um chunk de até
aproximadamente 1.000 caracteres e `Chunk.texto_para_embedding` acrescenta
`[caminho_heading]` quando há headings. O benchmark desta decisão usa frases
isoladas e, portanto, não mede o efeito desse contexto adicional.

O PostgreSQL usa pgvector e um índice HNSW com `vector_cosine_ops`. Na consulta
Django, `CosineDistance` devolve a distância de cosseno:

```text
distância de cosseno = 1 - similaridade de cosseno
```

Assim, `similaridade ≥ 0,66` e `distância ≤ 0,34` representam a mesma regra.

## Metodologia

O benchmark foi executado em 8 de outubro de 2026 com:

- Ollama 0.34.2;
- `nomic-embed-text`;
- vetores de 768 dimensões;
- textos em português;
- frases sem prefixos de tarefa do modelo, representando uma comparação
  requisito-a-requisito; essa entrada não reproduz os caminhos de heading nem
  o tamanho dos chunks de `api/ai/indexing.py`;
- uma única chamada batch ao endpoint `/api/embed`.

O dataset contém 30 pares rotulados:

| Grupo | Quantidade | Resultado esperado |
| --- | ---: | --- |
| Requisitos equivalentes | 10 | Exibir alerta |
| Mesmo domínio, intenção diferente | 10 | Não exibir alerta |
| Requisitos distintos | 10 | Não exibir alerta |

Os requisitos-base vieram do backlog do AI4PO. Para os casos equivalentes
foram criadas paráfrases controladas; para os casos negativos foram combinados
requisitos do mesmo domínio e de domínios diferentes. O dataset completo está
em [`scripts/similarity_pairs.json`](../../scripts/similarity_pairs.json).

O script calcula a similaridade de cosseno de cada par, avalia a matriz de
confusão para os pontos de corte e procura o melhor F1. O melhor corte medido
foi `0,654449`. Para não transformar uma medição pequena em uma constante
excessivamente específica, o valor foi arredondado para cima, resultando em
**0,66**. O arredondamento para cima também reduz falsos positivos, que geram
fadiga de alertas.

## Resultados

### Distribuição por grupo

| Grupo | Mínimo | Média | Máximo |
| --- | ---: | ---: | ---: |
| Requisitos equivalentes | 0,594014 | 0,671904 | 0,727155 |
| Mesmo domínio, intenção diferente | 0,526886 | 0,702548 | 0,886732 |
| Requisitos distintos | 0,521445 | 0,571077 | 0,650055 |

A sobreposição é relevante: alguns casos do mesmo domínio receberam scores
maiores do que todos os pares equivalentes. Isso ocorre porque termos e
estruturas muito parecidos podem dominar o embedding mesmo quando a intenção
da ação é diferente.

### Comparação de pontos de corte

| Similaridade mínima | VP | FP | VN | FN | Precisão | Recall | F1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0,55 | 10 | 14 | 6 | 0 | 0,42 | 1,00 | 0,59 |
| 0,60 | 8 | 12 | 8 | 2 | 0,40 | 0,80 | 0,53 |
| 0,65 | 8 | 8 | 12 | 2 | 0,50 | 0,80 | 0,62 |
| **0,66** | **7** | **5** | **15** | **3** | **0,58** | **0,70** | **0,64** |
| 0,70 | 3 | 4 | 16 | 7 | 0,43 | 0,30 | 0,35 |
| 0,75 | 0 | 4 | 16 | 10 | 0,00 | 0,00 | 0,00 |
| 0,80 | 0 | 2 | 18 | 10 | 0,00 | 0,00 | 0,00 |
| 0,85 | 0 | 1 | 19 | 10 | 0,00 | 0,00 | 0,00 |
| 0,90 | 0 | 0 | 20 | 10 | 0,00 | 0,00 | 0,00 |

No corte escolhido, a matriz de confusão foi:

- 7 verdadeiros positivos;
- 5 falsos positivos;
- 15 verdadeiros negativos;
- 3 falsos negativos;
- precisão de 58,3%, recall de 70,0% e F1 de 63,6%.

Os resultados completos, incluindo texto, score, distância e classificação de
cada par, estão em
[`resultados-benchmark-similaridade.csv`](resultados-benchmark-similaridade.csv).

### Casos que definem a limitação

Os falsos positivos mais fortes foram:

- criar uma Feature versus criar uma PBI: `0,886732`;
- autenticar versus recuperar senha: `0,800081`;
- desativar usuário versus alterar perfil de acesso: `0,789271`.

Os falsos negativos no corte 0,66 foram:

- analisar rascunho versus identificar lacunas: `0,654449`;
- alertar sobre requisitos semelhantes, em paráfrase: `0,594938`;
- exibir fontes do Chatbot, em paráfrase: `0,594014`.

Esses casos demonstram que elevar o corte para a faixa de 0,78–0,85 não reduz
somente ruído: neste dataset, essa faixa elimina todos os equivalentes e ainda
mantém falsos positivos.

## Diretriz para a task #7-2

Centralizar o valor em configuração, usando nomes que deixem explícita a
métrica:

```python
SIMILARITY_THRESHOLD = 0.66
MAX_COSINE_DISTANCE = 1.0 - SIMILARITY_THRESHOLD  # 0.34
```

Exemplo de consulta com Django e pgvector:

```python
from pgvector.django import CosineDistance

MAX_COSINE_DISTANCE = 0.34

similares = (
    ChunkDoc.objects
    .annotate(distance=CosineDistance("embedding", vetor_requisito))
    .filter(distance__lte=MAX_COSINE_DISTANCE)
    .order_by("distance")
)
```

Ao montar a resposta da API, a similaridade pode ser apresentada como
`1.0 - distance`. A implementação deve manter:

- o operador inclusivo (`>= 0,66` ou `<= 0,34`);
- o mesmo modelo de embedding na indexação e na consulta;
- uma representação de texto validada para os dois lados da comparação
  (requisito novo e chunk histórico, incluindo o efeito dos headings);
- ordenação por menor distância;
- origem do resultado (projeto e documento) para contextualizar o alerta.

Se o modelo, a dimensão, prefixos de tarefa ou o pré-processamento forem
alterados, os documentos devem ser reindexados e este benchmark deve ser
executado novamente antes de reutilizar o valor 0,66.

## Diretrizes para interface e testes

Como a precisão medida foi de 58,3%, a interface deve usar linguagem de
incerteza, por exemplo: **"Encontramos um possível requisito semelhante"**.
Não deve afirmar automaticamente que o requisito é duplicado.

Antes de liberar a task #7-2, a equipe deve acrescentar uma validação com
requisitos consultados contra chunks reais já indexados. Se essa amostra
alterar materialmente a matriz de confusão, o valor deve ser recalibrado e o
CSV atualizado; até essa validação, `0,66` é o ponto inicial para recuperação
de candidatos, não uma garantia para toda a base vetorial.

Na task #7-4, os testes de integração devem cobrir pelo menos:

1. similaridade exatamente igual a `0,66`: alerta exibido;
2. similaridade logo abaixo de `0,66`: alerta não exibido;
3. distância exatamente igual a `0,34`: resultado incluído;
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
e regenera `docs/technical-docs/resultados-benchmark-similaridade.csv`.
O script depende apenas da biblioteca padrão do Python.

Os testes unitários do cálculo e da seleção do limiar podem ser executados com:

```powershell
python -m unittest scripts.test_benchmark_similarity -v
```

## Limitações e próxima calibração

Trinta pares são suficientes para uma decisão inicial reproduzível, mas não
para uma garantia estatística de produção. Antes de considerar o limiar
estável, a equipe deve ampliar o dataset com requisitos históricos revisados
por pelo menos duas pessoas e registrar divergências de rotulagem.

Como critério de evolução, recomenda-se reavaliar o desenho quando houver
dados suficientes. Se a sobreposição permanecer, a busca vetorial deve ser
tratada como recuperação de candidatos e combinada com uma segunda etapa de
classificação de intenção, em vez de tentar resolver a ambiguidade apenas
aumentando o limiar.
