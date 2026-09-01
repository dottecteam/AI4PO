# Backlog da Sprint 1

| ID | User Story | Definição de Pronto | Definição de Feito | Estimativa |
|:---:|:---|:---|:---|:---:|
| #1 | Como usuário, desejo **entrar com minhas credenciais** para acessar as funcionalidades permitidas ao meu perfil. | - Fluxo de autenticação definido pela equipe;</br> - Stack de autenticação escolhida (JWT ou sessão);</br> - Layout da tela de login aprovado. | - Login funcional validando credenciais e criando a sessão;</br> - Rotas protegidas bloqueando usuários não autenticados;</br> - Mensagem de erro exibida para credenciais inválidas. |  |
| #2 | Como PO, desejo **cadastrar meus projetos** para que eles possam receber documentos e organizar a base de conhecimento. | - Campos obrigatórios do projeto definidos pela equipe;</br> - Modelagem da entidade de projeto concluída;</br> - Layout das telas aprovado. | - Cadastro de projetos funcionando e persistindo no banco;</br> - Validação de campos obrigatórios e de nome duplicado ativa;</br> - Projetos exibidos corretamente na listagem (edição fica para a Sprint 2). |  |
| #3 | Como PO, desejo **enviar documentos de um projeto** para que o histórico fique disponível na base de conhecimento. | - Formatos e tamanho máximo de arquivo definidos pela equipe;</br> - Estratégia de armazenamento dos arquivos escolhida;</br> - Layout da tela de documentos aprovado. | - Upload de documentos funcionando e associado ao projeto;</br> - Arquivos fora dos formatos suportados recusados com mensagem informativa;</br> - Falha de upload informando o erro e permitindo nova tentativa. |  |
| #4 | Como PO, desejo que os **documentos enviados sejam processados e indexados** para que fiquem pesquisáveis pela IA. | - Banco vetorial definido (ex.: pgvector);</br> - Serviço de embeddings escolhido;</br> - Estados de processamento definidos (pendente, processado, erro). | - Documentos processados e indexados na base vetorial após o upload;</br> - Estado de processamento visível na tela de documentos;</br> - Falha de processamento sinalizada com opção de reprocessamento. |  |
| #11 | Como PO, desejo **consultar no Chatbot como problemas técnicos foram resolvidos** em entregas passadas para não perder tempo. | - Base de conhecimento indexada nesta sprint;</br> - Prompt do Chatbot definido pela equipe;</br> - Layout da tela de conversa aprovado. | - Chatbot respondendo com base nos documentos indexados;</br> - Ausência de informação informada claramente, sem inventar resposta;</br> - Versão básica: turno único e sem citação de fontes (aprimoramentos na Sprint 3). |  |

---

## Tasks

| ID | Descrição | Definição de Pronto | Definição de Feito | Estimativa |
|:---:|:---|:---|:---|:---:|
| #1-1 | Modelar entidade de usuário no banco de dados (nome, e-mail, senha com hash, perfil: PO ou administrador). | - Perfis de acesso definidos pela equipe. | - Entidade `User` criada no banco e migration executada com sucesso. |  |
| #1-2 | Definir estratégia de sessão/token de autenticação. | - Entidade de usuário modelada. | - Estratégia (JWT ou sessão) escolhida e documentada em `/docs`. |  |
| #1-3 | Implementar rotas de login, logout e usuário atual na API. | - Estratégia de autenticação definida. | - Rota de login validando credenciais e retornando token/sessão válido; logout e usuário atual funcionais. |  |
| #1-4 | Implementar tela de login no frontend com validação de campos. | - Rotas de autenticação da API disponíveis;</br> - Layout aprovado pela equipe. | - Tela de login funcional consumindo a API e redirecionando o usuário autenticado conforme o perfil. |  |
| #1-5 | Proteger rotas do frontend e da API conforme o perfil do usuário. | - Autenticação funcionando. | - Usuários não autenticados redirecionados para o login; funcionalidades restritas ao perfil correto. |  |
| #1-6 | Realizar testes do fluxo de autenticação. | - Fluxo de login implementado. | - Cenários validados: login válido, credenciais inválidas e bloqueio de tentativas repetidas. |  |
| #2-1 | Modelar entidade de projeto e implementar rotas de cadastro e listagem com validações na API. | - Campos obrigatórios definidos pela equipe. | - Entidade criada com migration executada; endpoints criando e listando projetos com validação de campos obrigatórios e nome duplicado. |  |
| #2-2 | Implementar telas de listagem e cadastro de projetos no frontend. | - Rotas de cadastro disponíveis;</br> - Layout aprovado pela equipe. | - Telas funcionais: cadastro persiste os dados e listagem exibe os projetos cadastrados. |  |
| #2-3 | Realizar testes do fluxo de cadastro de projetos. | - Cadastro implementado. | - Cenários validados: cadastro com sucesso, campo obrigatório faltante e nome duplicado. |  |
| #3-1 | Definir formatos e tamanho máximo aceitos para upload de documentos. | - Escopo da base de conhecimento definido pela equipe. | - Documento `.md` criado em `/docs` listando formatos e limites, revisado pela equipe. |  |
| #3-2 | Modelar entidade de documento no banco de dados (projeto, arquivo, categoria, estado de processamento). | - Formatos aceitos definidos. | - Entidade `Document` criada no banco e migration executada com sucesso. |  |
| #3-3 | Implementar rota de upload de documentos com validação de formato e tamanho na API. | - Entidade de documento criada. | - Endpoint recebendo e armazenando arquivos válidos; arquivos inválidos recusados com mensagem dos formatos aceitos. |  |
| #3-4 | Configurar armazenamento dos arquivos enviados (disco ou cloud storage). | - Estratégia de armazenamento definida. | - Arquivos persistidos e recuperáveis pelo sistema. |  |
| #3-5 | Implementar tela de envio e listagem de documentos do projeto no frontend. | - Rota de upload disponível;</br> - Layout aprovado pela equipe. | - Usuário consegue enviar arquivos e visualizar a lista de documentos do projeto. |  |
| #3-6 | Realizar testes do fluxo de upload de documentos. | - Upload implementado. | - Cenários validados: upload válido, formato inválido e nova tentativa após falha. |  |
| #4-1 | Definir banco vetorial e serviço de embeddings a serem utilizados. | - Requisitos de busca da IA definidos pela equipe. | - Escolha documentada em `/docs` com justificativa e ambiente configurado. |  |
| #4-2 | Implementar extração de texto dos formatos de documento suportados. | - Formatos aceitos definidos. | - Módulo convertendo o conteúdo dos arquivos em texto processável. |  |
| #4-3 | Implementar pipeline de chunking e geração de embeddings. | - Extração de texto funcional;</br> - Banco vetorial configurado. | - Documentos enviados sendo convertidos em chunks vetorizados e armazenados na base vetorial. |  |
| #4-4 | Registrar estado de processamento dos documentos na API (pendente, processado, erro). | - Pipeline de indexação implementado. | - Estado atualizado corretamente conforme o resultado do processamento. |  |
| #4-5 | Exibir estado de processamento na tela de documentos no frontend. | - Estado disponível na API. | - Estado visível e atualizado junto a cada documento na listagem. |  |
| #4-6 | Implementar reprocessamento de documentos com falha. | - Estado de erro sinalizado na interface. | - Usuário consegue acionar o reprocessamento e o documento é reindexado com sucesso. |  |
| #4-7 | Realizar testes do pipeline de processamento e indexação. | - Pipeline completo implementado. | - Cenários validados: documento processado fica pesquisável; falha sinaliza erro e permite reprocessamento. |  |
| #11-1 | Implementar recuperação semântica (RAG) sobre a base vetorial para o Chatbot. | - Pipeline de indexação funcional. | - Perguntas retornando os trechos mais relevantes dos documentos indexados. |  |
| #11-2 | Definir prompt do Chatbot com restrição a não inventar respostas. | - Recuperação semântica funcional. | - Prompt criado e validado com perguntas de exemplo sobre os documentos indexados. |  |
| #11-3 | Implementar rota de pergunta/resposta na API (turno único). | - Prompt e recuperação prontos. | - Endpoint respondendo perguntas com base na base de conhecimento. |  |
| #11-4 | Implementar tela de conversa do Chatbot no frontend. | - Rota de resposta disponível;</br> - Layout aprovado pela equipe. | - Usuário consegue enviar perguntas e visualizar as respostas do Chatbot. |  |
| #11-5 | Realizar testes do fluxo básico do Chatbot. | - Fluxo implementado. | - Cenários validados: resposta com conteúdo relevante e ausência de informação informada sem inventar. |  |
