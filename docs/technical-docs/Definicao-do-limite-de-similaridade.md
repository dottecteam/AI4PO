# Limite de similaridade para alertas de requisitos

## Decisão

Para a primeira versão da feature #7, um requisito será considerado **possivelmente semelhante** quando:

- **similaridade de cosseno ≥ 0,81**; ou
- **distância de cosseno ≤ 0,19**.

Esses valores representam a mesma regra:

```text
distância = 1 - similaridade
```

O limite foi definido com base em um benchmark usando requisitos reais do AI4PO e o mesmo modelo de embeddings utilizado pelo sistema.

Com o corte de `0,81`, foram obtidos:

- **Precisão:** 88,9%
- **Recall:** 80,0%
- **F1:** 84,2%

Como a similaridade de texto não garante que dois requisitos tenham exatamente a mesma intenção, o sistema não deve afirmar que encontrou uma duplicidade.

A mensagem deve ser algo como:

**“Encontramos um possível requisito semelhante.”**

---

## Como funciona

O backend utiliza o Ollama com o modelo:

```text
nomic-embed-text
```

Esse modelo gera embeddings de **768 dimensões**.

O PostgreSQL utiliza pgvector e comparação por distância de cosseno.

No Django, `CosineDistance` retorna a distância entre os vetores. Por isso:

```text
similaridade >= 0,81
```

é equivalente a:

```text
distância <= 0,19
```

---

## Como o limite foi escolhido

Foram analisados **30 pares de requisitos reais**, divididos em três grupos:

| Grupo | Quantidade |
| --- | ---: |
| Requisitos equivalentes | 10 |
| Mesmo assunto, mas intenção diferente | 10 |
| Requisitos diferentes | 10 |

Os requisitos foram retirados dos Product Backlogs e Sprint Backlogs já existentes no projeto.

O script calculou a similaridade de cada par e testou diferentes limites.

O benchmark está em
[`api/ai/benchmark_similarity.py`](../../api/ai/benchmark_similarity.py) e usa
o próprio
[`resultados-benchmark-similaridade.csv`](resultados-benchmark-similaridade.csv)
como entrada e saída. A partir da pasta `api`, ele pode ser executado com:

```powershell
python -m ai.benchmark_similarity
```

Os testes do benchmark podem ser executados com:

```powershell
python -m unittest ai.test_benchmark_similarity -v
```

Os principais resultados foram:

| Limite | Precisão | Recall | F1 |
| ---: | ---: | ---: | ---: |
| 0,70 | 66,7% | 100% | 80,0% |
| 0,75 | 69,2% | 90% | 78,3% |
| 0,80 | 80% | 80% | 80,0% |
| **0,81** | **88,9%** | **80%** | **84,2%** |
| 0,85 | 83,3% | 50% | 62,5% |
| 0,90 | 100% | 10% | 18,2% |

O melhor resultado foi encontrado em aproximadamente `0,810202`.

Para facilitar a configuração, foi adotado **0,81**, pois isso não altera o resultado do benchmark.

---

## Resultado com o limite de 0,81

Com esse corte, tivemos:

- 8 requisitos equivalentes encontrados corretamente;
- 1 falso positivo;
- 19 requisitos diferentes ignorados corretamente;
- 2 requisitos equivalentes que não foram encontrados.

O falso positivo aconteceu entre dois requisitos relacionados ao Chatbot:

- conversar com o Chatbot;
- exibir as fontes utilizadas pelo Chatbot.

A similaridade entre eles foi `0,853015`.

Apesar da similaridade alta, os dois requisitos possuem objetivos diferentes.

Isso mostra que aumentar o limite não resolve completamente o problema.

Por exemplo, usando `0,85`, esse falso positivo continuaria existindo, enquanto vários requisitos realmente equivalentes deixariam de ser encontrados.

---

## Implementação

O valor deve ficar centralizado em uma configuração:

```python
SIMILARITY_THRESHOLD = 0.81
MAX_COSINE_DISTANCE = 0.19
```

Exemplo de consulta:

```python
from pgvector.django import CosineDistance

similares = (
    ChunkDoc.objects
    .annotate(
        distance=CosineDistance("embedding", vetor_requisito)
    )
    .filter(distance__lte=MAX_COSINE_DISTANCE)
    .order_by("distance")
)
```

Na resposta da API, a similaridade pode ser calculada assim:

```python
similarity = 1.0 - distance
```

A implementação deve:

- considerar `0,81` como valor válido;
- ordenar os resultados pela menor distância;
- informar de qual projeto e documento veio o requisito;
- usar o mesmo modelo de embeddings na indexação e na busca;
- tratar o resultado apenas como uma possível semelhança.

---

## Testes

Os testes de integração devem verificar pelo menos:

1. similaridade igual a `0,81` deve gerar alerta;
2. valor abaixo de `0,81` não deve gerar alerta;
3. distância igual a `0,19` deve ser aceita;
4. resultados devem ser ordenados pela menor distância;
5. a origem do requisito deve ser retornada;
6. sem candidatos dentro do limite, nenhum alerta deve aparecer.

---

## Limitações

O benchmark utiliza apenas **30 pares de requisitos de um único projeto**, então o valor `0,81` não deve ser tratado como definitivo.

Além disso, a busca real utiliza `ChunkDoc`, que pode trabalhar com trechos maiores e incluir headings no texto enviado ao modelo.

Por isso, o comportamento deve ser acompanhado durante a implementação.

Se no futuro forem alterados:

- o modelo de embeddings;
- a forma de preparar o texto;
- a dimensão dos vetores;
- ou a forma de dividir os documentos;

o benchmark deve ser executado novamente.

Com mais requisitos históricos disponíveis, o dataset também deve ser ampliado.

Se ainda houver muitos casos ambíguos, a busca por embeddings pode ser usada apenas para encontrar candidatos, deixando uma segunda etapa responsável por decidir se os requisitos realmente possuem a mesma intenção.
