# Justificativa da Escolha do Qwen3.5 4B

Para o projeto **AI4PO**, foi escolhido o modelo **Qwen3.5 4B**, executado localmente por meio do **Ollama**.

A escolha considera principalmente a necessidade de executar a IA localmente, reduzindo a dependência de serviços externos e permitindo maior controle sobre os dados utilizados pelo sistema. Isso é importante porque o AI4PO trabalhará com informações internas, como documentos, projetos, backlog e registros de reuniões.

O Qwen3.5 4B apresenta um bom equilíbrio entre **capacidade do modelo e consumo de recursos**. Sua versão disponibilizada pelo Ollama possui aproximadamente **3,4 GB** e suporta contexto de até **256K tokens**, além de texto e imagem.

Para o AI4PO, o modelo será utilizado em conjunto com **RAG e PostgreSQL + pgvector**. Dessa forma, o conhecimento da organização não precisa estar armazenado diretamente no modelo. Os documentos são transformados em embeddings, armazenados no banco vetorial e posteriormente recuperados para fornecer contexto ao Qwen3.5 4B.

```text
Documentos
    ↓
Embeddings
    ↓
PostgreSQL + pgvector
    ↓
Busca semântica
    ↓
Contexto relevante
    ↓
Qwen3.5 4B
    ↓
Resposta
```

---

Outro fator importante é o hardware. O modelo pode ser executado em máquinas com **8 GB de RAM**, embora esse cenário seja mais limitado quando outros serviços do projeto estiverem rodando simultaneamente. Por isso, **16 GB de RAM é o recomendado para executar todo o ambiente do AI4PO**, incluindo Docker, Django, Next.js, PostgreSQL e Ollama.

Modelos menores, como o Qwen3.5 2B, podem ser utilizados em máquinas com menos recursos, enquanto modelos maiores, como o Qwen3.5 9B, podem oferecer maior capacidade em máquinas mais potentes.

Assim, o **Qwen3.5 4B foi escolhido por oferecer um equilíbrio adequado entre qualidade, consumo de recursos, execução local e integração com a arquitetura RAG do AI4PO**.
