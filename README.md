# AI4PO — Inteligência Artificial para Product Owners

## Conceito do Nome

O **AI4PO** (*Artificial Intelligence for Product Owners*) é uma plataforma desenvolvida para auxiliar **Product Owners (POs)** no gerenciamento e na análise de informações relacionadas aos produtos e projetos de software.

A proposta combina **Inteligência Artificial, Recuperação Aumentada por Geração (RAG) e dados históricos da organização**, permitindo que os POs consultem informações, analisem projetos anteriores e obtenham apoio na elaboração e organização de novos itens de backlog.

O sistema busca transformar o conhecimento acumulado pela empresa em uma **base de conhecimento inteligente**, facilitando a tomada de decisões e reduzindo o tempo necessário para consultar informações espalhadas em diferentes documentos e projetos.

---

## Descrição

O **AI4PO** é uma plataforma web que utiliza Inteligência Artificial para auxiliar Product Owners na gestão de produtos e projetos de software.

A aplicação centraliza informações como:

- Projetos anteriores
- Backlogs
- User Stories
- Tasks
- Requisitos
- Reuniões e atas
- Documentação
- Decisões tomadas ao longo dos projetos

Esses dados são processados e disponibilizados para um sistema de **RAG (Retrieval-Augmented Generation)**, permitindo que o usuário faça perguntas à IA utilizando o conhecimento da própria organização como contexto.

Além de consultar informações existentes, o PO poderá utilizar a IA como apoio na **criação, refinamento e análise de itens de backlog**.

---

## MVP

O desenvolvimento do **AI4PO** está estruturado em sprints, evoluindo progressivamente desde a fundação técnica até a integração da Inteligência Artificial.

---

## Backlog do Produto (Resumo)

Abaixo estão algumas das principais funcionalidades previstas para o sistema:

# Backlog do Produto — AI4PO (Pro4Tech)

| ID | User Story | Prioridade | Estimativa | Sprint |
| :-: | :--- | :-: | :-: | :-: |
| #1 | Como usuário, quero **entrar com minhas credenciais** para acessar o sistema de acordo com meu perfil. | Alta | 3 | 1 |
| #2 | Como PO, quero **criar projetos** para organizar as informações de cada projeto. | Alta | 5 | 1 |
| #3 | Como PO, quero **enviar documentos do projeto para que sejam processados** e fiquem disponíveis na base de conhecimento. | Alta | 8 | 1 |
| #4 | Como sistema, quero **indexar as informações dos documentos** para permitir que a IA encontre conteúdos relevantes. | Alta | 8 | 1 |
| #5 | Como PO, quero **conversar com o Chatbot** para consultar o conhecimento e as informações de projetos anteriores de forma mais simples. | Alta | 8 | 1 |
| #6 | Como administrador, quero **gerenciar os usuários** para controlar quem pode acessar a plataforma. | Alta | 5 | 2 |
| #7 | Como PO, quero **editar as informações de um projeto** para manter seus dados atualizados. | Alta | 3 | 2 |
| #8 | Como PO, quero **criar, visualizar e editar uma Feature dentro de um projeto** para organizar as funcionalidades que serão trabalhadas. | Alta | 5 | 2 |
| #9 | Como PO, quero **criar e editar requisitos de uma Feature** para registrar o que precisa ser desenvolvido. | Alta | 5 | 2 |
| #10 | Como PO, quero **enviar uma especificação para análise da IA** e receber sugestões sobre meus requisitos com base em requisitos semelhantes de projetos anteriores, para identificar lacunas e melhorar a qualidade da especificação. | Alta | 13 | 2 |
| #11 | Como PO, quero **padronizar meus requisitos e gerar uma especificação organizada** de acordo com o padrão da Pro4Tech para facilitar sua documentação. | Alta | 8 | 2 |
| #12 | Como PO, quero **exportar os requisitos e especificações** para utilizá-los em outras ferramentas da equipe. | Alta | 5 | 2 |
| #13 | Como PO, quero **ver as fontes utilizadas pelo Chatbot** para verificar de onde vieram as informações da resposta. | Média | 5 | 3 |
| #14 | Como PO, quero **receber sugestões de documentos relacionados à minha pesquisa** para encontrar informações relevantes. | Média | 5 | 3 |
| #15 | Como gestor, quero **registrar as competências e projetos dos times** para manter o conhecimento profissional disponível na plataforma. | Média | 5 | 3 |
| #16 | Como gestor, quero **buscar profissionais por competência** para encontrar pessoas com conhecimentos adequados para cada necessidade. | Média | 8 | 3 |
| #17 | Como gestor, quero **consultar o histórico dos profissionais** para conhecer suas experiências em projetos anteriores. | Média | 3 | 3 |
| #18 | Como usuário, quero **consultar o histórico de alterações dos itens do projeto e registrar justificativas para as alterações**, para acompanhar a evolução do projeto e preservar o contexto das decisões tomadas. | Média | 5 | 3
| #19 | Como líder, quero **acessar o manual da plataforma** para entender como utilizar a solução. | Baixa | 3 | 3 |

---

## Tecnologias Utilizadas

### Frontend

![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)

- **Next.js** para construção da aplicação web
- **React** para desenvolvimento da interface
- **TypeScript** para tipagem e maior segurança no desenvolvimento
- Interface responsiva para utilização pelos Product Owners

---

### Backend

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)

- **Django** como framework principal do backend
- **Django REST Framework** para construção da API REST
- Organização do sistema através de aplicações Django
- Gerenciamento de usuários, projetos, backlog e funcionalidades de IA

---

### Banco de Dados

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

- **PostgreSQL** como banco de dados principal
- **pgvector** para armazenamento e busca de embeddings
- Persistência de projetos, usuários, backlog e informações estruturadas
- Armazenamento vetorial para suporte ao sistema RAG

A utilização do pgvector permite combinar os dados tradicionais do PostgreSQL com **busca por similaridade semântica**.

---

### Inteligência Artificial

![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)

- **Ollama** para execução local dos modelos de linguagem
- **LLM** para geração das respostas
- **Embeddings** para representação vetorial dos documentos
- **RAG (Retrieval-Augmented Generation)** para fornecer contexto à IA
- Possibilidade de utilização de modelos locais sem depender diretamente de APIs externas

O modelo não depende apenas de seu conhecimento pré-treinado. Antes de responder, o sistema pode buscar informações relevantes na base de conhecimento da empresa e utilizá-las como contexto.

---

### Infraestrutura

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

- **Docker** para isolamento dos serviços
- **Docker Compose** para orquestração do ambiente
- Ambiente padronizado para desenvolvimento
- Separação entre frontend, backend, banco de dados e IA

---

# Como Executar com Docker (Recomendado)

A maneira recomendada de executar o ecossistema do **AI4PO** é utilizando Docker Compose.

## 1. Pré-requisitos

- **Docker** instalado
- **Docker Compose** disponível
- Git instalado
- Arquivo `.env` configurado

## 2. Clonar o projeto

```bash
git clone <URL_DO_REPOSITORIO>
cd AI4PO
```

## 3. Configurar as variáveis de ambiente

Crie o arquivo `.env` na raiz do projeto:

```env

Configurações do Banco de Dados PostgreSQL (vetorial)
POSTGRES_DB=ai4po
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

URL de conexão com a Inteligência Artificial Local
OLLAMA_URL=http://ollama:11434

Configurações do Django (Backend)
SECRET_KEY=ai4po
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

> Não versione o arquivo `.env`. Utilize um `.env.example` para documentar as variáveis necessárias.

## 4. Subir o projeto

Na raiz do repositório:

```bash
docker compose up --build
```

Ou, para executar em segundo plano:

```bash
docker compose up --build -d
```

Isso iniciará os principais serviços da aplicação:

- **Frontend:** `http://localhost:3000`
- **Backend:** `http://localhost:8000`
- **PostgreSQL:** `localhost:5432`
- **Ollama:** `http://localhost:11434`

## 5. Verificar os containers

```bash
docker compose ps
```

Para visualizar os logs:

```bash
docker compose logs -f
```

Para encerrar os serviços:

```bash
docker compose down
```

---

# Execução Local

Caso não queira utilizar Docker durante o desenvolvimento, frontend e backend também podem ser executados separadamente.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

O Next.js ficará disponível em:

```text
http://localhost:3000
```

### Backend

```bash
cd backend

python -m venv venv
```

No Windows:

```powershell
venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute o Django:

```bash
python manage.py runserver
```

O backend ficará disponível em:

```text
http://localhost:8000
```

---

## Colaboradores

Nome | Função | LinkedIn | GitHub
-|-|-|-
Cauã Mehiel | Scrum Master | [![LinkedIn](https://img.shields.io/badge/linkedin-blue?style=for-the-badge)](https://www.linkedin.com/in/cau%C3%A3-cursino-748485235) | <a href="https://github.com/CauaCurisno1446"> <img src="https://img.shields.io/badge/github-black?style=for-the-badge&logo=github"/> </a>
Kayan da Matta | Product Owner | [![LinkedIn](https://img.shields.io/badge/linkedin-blue?style=for-the-badge)](https://www.linkedin.com/in/joaosantos02) | <a href="https://github.com/kayanmatta"> <img src="https://img.shields.io/badge/github-black?style=for-the-badge&logo=github"/> </a>
Davi Andrade | Developer | [![LinkedIn](https://img.shields.io/badge/linkedin-blue?style=for-the-badge)](https://www.linkedin.com/in/daviandrade007) | <a href="https://github.com/aandrade007"> <img src="https://img.shields.io/badge/github-black?style=for-the-badge&logo=github"/> </a>
João Paulo | Developer | [![LinkedIn](https://img.shields.io/badge/linkedin-blue?style=for-the-badge)](https://www.linkedin.com/in/joaosantos02) | <a href="https://github.com/jopaul0"> <img src="https://img.shields.io/badge/github-black?style=for-the-badge&logo=github"/> </a>
Kauan Domingues | Developer | [![LinkedIn](https://img.shields.io/badge/linkedin-blue?style=for-the-badge)](https://linkedin.com/in/kauandomingues) | <a href="https://github.com/KauanDomingues"> <img src="https://img.shields.io/badge/github-black?style=for-the-badge&logo=github"/> </a>
Gabriel Borges | Developer | [![LinkedIn](https://img.shields.io/badge/linkedin-blue?style=for-the-badge)](https://www.linkedin.com/in/gabriel-borges-toledo) | <a href="https://github.com/Gabe-Borges"> <img src="https://img.shields.io/badge/github-black?style=for-the-badge&logo=github"/> </a>
Jessica Katayama | Developer | [![LinkedIn](https://img.shields.io/badge/linkedin-blue?style=for-the-badge)](https://www.linkedin.com/in/jessicakatayama) | <a href="https://github.com/JessicaKatayama"> <img src="https://img.shields.io/badge/github-black?style=for-the-badge&logo=github"/> </a>
Marya Vitória | Developer | [![LinkedIn](https://img.shields.io/badge/linkedin-blue?style=for-the-badge)](https://www.linkedin.com/in/nicolas-anderson-34b082302) | <a href="https://github.com/mavygarcia"> <img src="https://img.shields.io/badge/github-black?style=for-the-badge&logo=github"/> </a>


