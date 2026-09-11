# Justificativa Banco Vetorial e Serviço de Embeddings

# 1. Contexto
O AI4PO utiliza a arquitetura RAG (Retrieval-Augmented Generation) para permitir que Product Owners consultem o histórico de projetos da empresa. Para que isso funcione, precisamos de um serviço para transformar textos em representações numéricas (embeddings) e um banco de dados capaz de armazenar e realizar buscas por similaridade semântica (banco vetorial).

# 2. Decisões Tomadas

## 2.1 Banco Vetorial: PostgreSQL + pgvector
Decisão: Utilizaremos o PostgreSQL como banco de dados principal, integrado à extensão pgvector.
Justificativa: Infraestrutura Unificada: O PostgreSQL já foi escolhido para armazenar os dados relacionais do sistema (usuários, projetos, backlogs via Django). O pgvector permite armazenar os embeddings na mesma infraestrutura, reduzindo a complexidade de manter múltiplos bancos de dados.

## 2.2 Serviço de Embeddings: Ollama
Decisão: Utilizaremos o Ollama para a geração de embeddings e, posteriormente, para a execução do modelo de linguagem (LLM).
Justificativa: Privacidade e Segurança: O AI4PO processa documentos internos e estratégicos da organização. O Ollama permite executar modelos open-source (como Llama 3 ou Mistral) de forma 100% local, garantindo que nenhum dado sensível saia da infraestrutura da empresa.
Custo: A execução local elimina a necessidade de pagar por consumo de APIs externas.

Padronização do Ambiente: O Ollama será integrado via Docker, mantendo o ambiente de desenvolvimento consistente para toda a equipe.

# 3. Configuração Prática do Ambiente e Lições Aprendidas
Para garantir que o ambiente de desenvolvimento seja idêntico para toda a equipe, utilizamos o Docker e o Docker Compose, orquestrando quatro serviços principais: Banco de Dados (db), Backend (backend), Frontend (frontend) e IA Local (ollama).

## 3.1 O Papel do Arquivo .env (Cofre de Credenciais)
•	O que é: Um arquivo local situado na raiz do projeto que armazena variáveis sensíveis e de configuração, impedindo que dados críticos sejam expostos no repositório de código.
•	Variáveis Utilizadas:
- POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD: Credenciais de acesso ao banco de dados relacional.
- OLLAMA_URL: Endereço de comunicação com o serviço de inteligência artificial.
- SECRET_KEY, DEBUG, ALLOWED_HOSTS: Parâmetros de segurança e execução obrigatórios do framework Django (Backend).

## 3.2 Estrutura do Docker Compose (docker-compose.yml)
- Banco de Dados (db): Utilizamos a imagem oficial pgvector/pgvector:pg16. A escolha por esta imagem garante que o PostgreSQL nativo já venha com a extensão de vetores habilitada nativamente, suportando o armazenamento dos chunks e embeddings do RAG.
- Persistência de Dados (volumes): Configuramos volumes dedicados (como o postgres_data) para garantir que as informações salvas no banco não sejam perdidas caso os contêineres sejam desligados ou reiniciados.

## 3.3 Problemas Comuns e Soluções (Troubleshooting)
Caso o ambiente apresente falhas ao ser executado no Windows, utilize esta referência rápida:
•	Backend desligando sozinho: Geralmente ocorre por ausência de variáveis obrigatórias no .env (como a SECRET_KEY) ou porque o backend tentou subir antes do banco de dados estar totalmente pronto. Solução: Validar o arquivo .env e utilizar o parâmetro depends_on no Docker Compose para ordenar a inicialização correta dos serviços.
