# Manual do usuário — AI4PO

Versão deste manual: 1.0  
Última atualização: novembro de 2026

O **AI4PO** é uma plataforma web para consulta do conhecimento organizacional e organização de projetos, documentos e itens de backlog. As informações desta versão referem-se às funcionalidades disponíveis na interface atual.

Este manual foi elaborado para os perfis:

- **Product Owner (PO)**: trabalha com projetos, documentos, backlog, chatbot e grafos.
- **Administrador**: executa todas as ações do PO e também gerencia o estado dos logins existentes.

## Índice

1. [Antes de começar](#1-antes-de-começar)
2. [Acessar e sair da plataforma](#2-acessar-e-sair-da-plataforma)
3. [Conhecer a navegação](#3-conhecer-a-navegação)
4. [Perfil PO](#4-perfil-po)
   - [Página Inicial](#41-página-inicial)
   - [Projetos](#42-projetos)
   - [Documentos](#43-documentos)
   - [Backlog](#44-backlog)
   - [ChatBot / Novo Chat](#45-chatbot)
   - [Meu Perfil](#47-meu-perfil)
   - [Profissionais](#48-profissionais)
   - [Competências](#49-competências)
   - [Grafo de Conhecimento](#410-grafo-de-conhecimento)
5. [Perfil administrador](#5-perfil-administrador)
6. [Boas práticas](#6-boas-práticas)
7. [Perguntas frequentes e solução de problemas](#7-perguntas-frequentes-e-solução-de-problemas)

---

## 1. Antes de começar

### 1.1 Endereços

Em ambiente local, os principais endereços são:

| Recurso | Endereço |
| --- | --- |
| Aplicação web | `http://localhost:3000` |
| API do sistema | `http://localhost:8000` |

Em ambientes corporativos ou de produção, use os endereços fornecidos pela equipe responsável.

### 1.2 Navegadores

Utilize uma versão atualizada de navegador moderno, como Microsoft Edge, Google Chrome, Mozilla Firefox ou Safari. Para evitar perda de sessão, não exclua os cookies do domínio da aplicação enquanto estiver trabalhando.

### 1.3 Contas e permissões

A plataforma não oferece cadastro público. Uma conta é criada pela equipe responsável ou pelo administrador técnico da instalação.

- Contas comuns acessam as áreas destinadas ao PO.
- Contas administradoras têm acesso às áreas de PO e à **Administração de logins**.
- A conta de um usuário desativado não consegue acessar o sistema.
- O perfil de administrador não é alterado pela tela de usuários.

---

## 2. Acessar e sair da plataforma

### 2.1 Entrar

1. Abra o endereço da AI4PO.
2. Informe o **E-mail corporativo**.
3. Informe a **Senha**.
4. Selecione **Entrar na Plataforma**.

Mensagens possíveis:

- **E-mail ou senha incorretos**: confira os dados digitados.
- **Você precisa fazer login para acessar o painel**: a sessão terminou ou o acesso foi solicitado sem autenticação.
- **Falha de conexão com o servidor**: confira sua rede e se os serviços da aplicação estão disponíveis.

Ao entrar, a plataforma abre a **Página Inicial**.

### 2.2 Encerrar a sessão

1. Abra **Meu Perfil** no menu lateral.
2. Na seção **Sessão**, selecione **Sair da conta**.
3. Aguarde o redirecionamento para a tela de entrada.

A plataforma possui uma rota interna para limpar os cookies de sessão. Ela pode ser acionada automaticamente pelo sistema ao detectar uma sessão inválida ou expirada.

O sistema também pode redirecionar para o login quando o token expira ou quando um administrador desativa ou altera o login.

---

## 3. Conhecer a navegação

### 3.1 Menu lateral

O menu lateral apresenta os seguintes itens principais:

| Item | Uso |
| --- | --- |
| **Página Inicial** | Tela de boas-vindas. |
| **Novo Chat** | Conversar com o assistente e consultar a base de conhecimento. |
| **Projetos** | Pesquisar, criar e abrir projetos. |
| **Grafo Global** | Visualizar entidades e relações de todos os projetos. |
| **Profissionais** | Cadastrar profissionais, buscar afinidade por competências e consultar trajetórias. |
| **Competências** | Cadastrar, renomear e organizar o catálogo de competências. |
| **Meu Perfil** | Consultar dados da conta, trajetória profissional e encerrar a sessão. |
| **Administração** | Gerenciar os logins; disponível somente para administradores. |

### 3.2 Histórico Recente

Quando o menu lateral está expandido, a área **Histórico Recente** lista as conversas disponíveis. Cada conversa mostra:

- título salvo pela plataforma;
- indicação de “HOJE”, “ONTEM” ou data aproximada;
- destaque da conversa atualmente aberta.

Selecione uma conversa para carregar suas mensagens. Recarregar ou sair da página não exclui conversas já salvas.

### 3.3 Menu em telas pequenas

Em celulares e telas estreitas:

1. Selecione o botão de menu no canto superior esquerdo.
2. Escolha uma opção.
3. O menu fecha automaticamente após a troca de página.

No computador, o botão no menu lateral recolhe ou expande a barra lateral.

### 3.4 Navegação entre níveis

Dentro de um projeto, use o **breadcrumb** no topo para voltar ao projeto, à lista de projetos ou a uma Feature ou Épico anterior.

Os níveis usados pelo backlog são:

```text
Projeto
└── Épico
    └── Feature
        └── PBI
```

---

## 4. Perfil PO

### 4.1 Página Inicial

A Página Inicial mostra uma tela de boas-vindas. Nesta versão, ela não apresenta indicadores, gráficos ou relatórios.

Use o menu lateral para acessar:

- **Projetos**, para cadastrar ou atualizar informações;
- **Novo Chat**, para consultas e análise assistida;
- **Grafo Global**, para explorar relações conhecidas.

---

### 4.2 Projetos

#### 4.2.1 Pesquisar projetos

1. Selecione **Projetos** no menu.
2. No campo **Pesquise por títulos de projetos**, digite parte do título.
3. Use o botão de filtro para escolher status:
   - **Rascunho**;
   - **Ativo**;
   - **Inativo**.
4. Use o filtro de data para informar um período de criação.
5. Limpe os filtros selecionados para voltar à lista completa.

A área pode mostrar um filtro de PO com opções de exemplo. Esse filtro não representa necessariamente a lista oficial de usuários cadastrados.

A página informa **Nenhum projeto a exibir** quando não existe projeto ou quando nenhum registro corresponde aos critérios.

#### 4.2.2 Cadastrar um projeto

1. Selecione o botão `+` na seção **Projetos**.
2. Preencha:
   - **Título**;
   - **Descrição**;
   - **Status**;
   - **PO**, no campo numérico exibido pelo formulário.
3. Selecione **Cadastrar**.

Todos os campos precisam ser preenchidos. Se algo estiver faltando, a tela informa: **Todos os campos devem ser preenchidos**.

Na versão atual, o PO responsável pelo projeto criado é definido pela conta que está autenticada. Apesar de o formulário exibir um campo numérico de PO, o backend não permite que o cadastro mova a posse para outro usuário. Portanto, informe o identificador como solicitado pela interface, mas considere o usuário conectado como responsável da criação.

O status inicial sugerido é **Rascunho**. Use:

- **Rascunho** enquanto o projeto ainda está sendo estruturado;
- **Ativo** para projetos em andamento;
- **Inativo** para projetos concluídos ou suspensos.

Ao cadastrar, o modal é fechado e o projeto aparece na lista.

#### 4.2.3 Abrir e consultar um projeto

Na lista, selecione o cartão do projeto. A página do projeto apresenta:

- título;
- status;
- responsável informado como PO;
- data de criação;
- descrição;
- lista de épicos;
- documentos;
- grafo de conhecimento.

As seções podem ser abertas ou recolhidas por meio da interface.

#### 4.2.4 Editar um projeto

1. Abra o projeto.
2. Selecione o menu de três pontos no canto superior direito.
3. Selecione **Editar**.
4. Altere o título, a descrição ou o status.
5. Selecione **Confirmar** para salvar.

Para desistir, selecione **Cancelar**. Ao cancelar, os valores retornam aos dados anteriores.

#### 4.2.5 Excluir um projeto

1. Abra o projeto.
2. Selecione o menu de três pontos.
3. Selecione **Excluir**.

Exclusões podem afetar dados associados ao projeto. Confirme a necessidade com o responsável antes de excluir. A interface atual não apresenta uma confirmação adicional no modal de exclusão.

---

### 4.3 Documentos

Os documentos fornecem o conteúdo usado pela pesquisa, pelo chatbot e pela geração do grafo de conhecimento.

#### 4.3.1 Preparar um arquivo

Antes do envio, confirme:

- formato **TXT** ou **MD**;
- tamanho máximo de **10 MB**;
- conteúdo legível e organizado;
- nome do arquivo claro.

Arquivos PDF, DOCX, imagens e outros formatos não são aceitos por esta versão.

#### 4.3.2 Enviar um documento

1. Abra o projeto.
2. Expanda a seção **Documentos**.
3. Selecione o botão de adicionar.
4. Selecione **Arquivo (.txt ou .md)**.
5. Confirme o arquivo selecionado.
6. Selecione **Enviar**.

A tela possui duas fases:

1. **Enviando**: acompanha o envio com porcentagem e tempo restante estimado.
2. **Gerando grafo de conhecimento (GraphRAG)**: acompanha o processamento da base e do grafo.

Durante a geração do grafo, aguarde ou feche a janela somente após a conclusão indicada pela interface. A janela também pode fechar automaticamente após o processamento.

Os estados possíveis são:

| Estado | Significado |
| --- | --- |
| **Pendente** | O arquivo foi registrado e aguarda processamento. |
| **Processando** | O conteúdo está sendo indexado ou analisado. |
| **Processado** | O processamento foi concluído com sucesso. |
| **Erro** | O processamento falhou e pode existir uma mensagem explicativa. |

Quando há documentos pendentes ou em processamento, a lista é atualizada automaticamente a cada alguns segundos.

#### 4.3.3 Pesquisar e filtrar documentos

Na seção **Documentos**:

1. Use o campo **Pesquise por nomes de documentos**.
2. Abra o filtro **Extensão** e selecione uma das extensões cadastradas no projeto. Os arquivos aceitos pelo upload são `.txt` e `.md`.
3. Use o filtro de data para limitar por intervalo de envio.
4. Combine filtros para obter a lista desejada.

#### 4.3.4 Reprocessar um documento

Use o reprocessamento quando o documento estiver com estado **Erro**.

1. Selecione o menu de três pontos do documento.
2. Selecione **Reprocessar**.
3. Aguarde o estado voltar para processando ou processado.

O reprocessamento pode corrigir falhas temporárias de indexação ou de geração do grafo. Se o erro persistir, registre o nome do projeto, o nome do arquivo e a mensagem exibida e envie à equipe responsável.

---

### 4.4 Backlog

O backlog é organizado em quatro níveis:

```text
Projeto → Épico → Feature → PBI
```

Use os títulos e descrições de forma objetiva. Dados específicos devem ser registrados nos campos próprios de cada formulário.

#### 4.4.1 Criar um Épico

1. Abra o projeto.
2. Na tabela de épicos, selecione o botão de adicionar.
3. Preencha:
   - **Título**;
   - **Descrição**;
   - **Objetivo**;
   - **Resultado esperado**;
   - **Escopo Macro**;
   - **Critérios de Aceitação**.
4. Em listas internas, use **Adicionar Capacidade** ou **Adicionar Critério**.
5. Selecione **Cadastrar**.

Todos os campos principais devem ser preenchidos. Escopo Macro e Critérios de Aceitação permitem vários itens.

#### 4.4.2 Consultar um Épico

Selecione o épico na tabela para abrir sua página. Use o menu de três pontos do épico para editar ou excluir.

A edição permite alterar título, descrição, objetivo, resultado esperado, escopo macro e critérios de aceitação.

#### 4.4.3 Criar uma Feature

1. Abra o Épico.
2. Selecione o botão de adicionar da seção de Features.
3. Preencha:
   - **Título**;
   - **Descrição**;
   - **Objetivo**;
   - **Critérios de Aceitação**.
4. Use **Adicionar Critério** quantas vezes forem necessárias.
5. Selecione **Cadastrar**.

#### 4.4.4 Consultar e editar uma Feature

Selecione a Feature na tabela para ver seus dados e PBIs associados. Pelo menu de três pontos, use **Editar** para atualizar os campos ou **Excluir** para remover o item.

#### 4.4.5 Criar um PBI

1. Abra a Feature.
2. Selecione o botão de adicionar na seção de PBIs.
3. Preencha o **Título**.
4. Preencha a **User Story**:
   - **Como**;
   - **Quero**;
   - **Para que**.
5. Opcionalmente, registre **Regras / observações**.
6. Adicione cenários no formato:
   - **Dado**;
   - **Quando**;
   - **Então**.
7. Selecione **Cadastrar**.

O título e todos os componentes da User Story são obrigatórios. Cenários são opcionais, mas úteis para detalhar comportamento esperado e casos de teste.

#### 4.4.6 Similaridade ao cadastrar PBI

Ao preencher o título e os componentes da User Story, a tela consulta PBIs semelhantes. Um alerta pode mostrar:

- título do PBI parecido;
- projeto de origem;
- porcentagem ou nível de similaridade;
- justificativa ou trecho relacionado.

Use o alerta como apoio à revisão. Ele não impede automaticamente o cadastro e não substitui a análise do PO. É importante verificar se o conteúdo já existe, se pode ser reutilizado ou se representa uma necessidade realmente diferente.

#### 4.4.7 Consultar, editar ou excluir PBI

1. Abra o PBI pela tabela da Feature.
2. Consulte o título, User Story, cenários e regras.
3. Pelo menu de três pontos, selecione **Editar** ou **Excluir**.

Ao editar, revise especialmente os componentes **Como**, **Quero** e **Para que**, pois eles descrevem quem se beneficia da necessidade, a ação desejada e o objetivo.

---

### 4.5 ChatBot

O ChatBot usa a base de conhecimento da plataforma para responder com contexto. Para documentos ou projetos novos terem valor nas respostas, eles precisam ter sido enviados e processados.

#### 4.5.1 Iniciar uma conversa

1. Selecione **Novo Chat** no menu.
2. Digite a pergunta no campo inferior.
3. Pressione **Enter** para enviar.
4. Use **Shift+Enter** para quebrar linha sem enviar.

O botão de envio só é habilitado quando existe texto ou um arquivo anexado.

#### 4.5.2 Recuperar conversa anterior

1. Expanda o menu lateral.
2. Procure a conversa em **Histórico Recente**.
3. Selecione o título.

Ao abrir uma conversa existente, as mensagens já registradas são carregadas.

#### 4.5.3 Consultar fontes

Quando a resposta foi produzida com fontes recuperadas, a área abaixo da mensagem pode apresentar **Fontes (quantidade)**.

Selecione a linha **Fontes** para visualizar:

- projeto;
- documento;
- seção, quando disponível;
- trecho recuperado;
- percentual de similaridade.

Sempre confira as fontes antes de transformar uma resposta em requisito ou decisão. A IA pode apresentar informações incompletas ou não verificar o contexto organizacional.

#### 4.5.4 Anexar um arquivo à conversa

É possível enviar um arquivo junto de uma mensagem, sem necessariamente cadastrá-lo na base de conhecimento do projeto.

1. Selecione o botão de anexar.
2. Escolha um arquivo `.txt` ou `.md` de até 10 MB.
3. Digite uma pergunta ou instrução no campo de mensagem.
4. Selecione enviar.

Regras:

- somente um arquivo por mensagem;
- arquivo sem texto não é enviado ao backend;
- ao selecionar um arquivo sem texto, ele pode aparecer apenas como um card visual;
- o formato enviado à conversa não substitui o envio à seção **Documentos** do projeto.

Para tornar o arquivo permanentemente disponível como conteúdo do projeto, use **Documentos → Adicionar**.

#### 4.5.5 Usar `/validar`

O comando `/validar` solicita a validação de requisitos apresentados na conversa.

Exemplo:

```text
/validar
Como cliente, quero consultar meus pedidos para acompanhar o status da entrega.
O sistema deve enviar uma confirmação por e-mail.
```

O sistema retorna um cartão de validação contendo:

- **Especificação em conformidade** ou **Pendências encontradas**;
- número de regras aprovadas;
- erros;
- avisos;
- observações.

Use os erros e avisos para revisar o texto. A conformidade é uma análise automática e requer julgamento do PO.

#### 4.5.6 Usar `/reformatar`

O comando `/reformatar` solicita que os requisitos sejam reorganizados conforme o padrão esperado pela plataforma.

Exemplo:

```text
/reformatar
O usuário precisa alterar seu endereço.
Deve ser possível salvar o novo endereço e confirmar a alteração.
```

Revise o resultado antes de usar em projeto, épico, Feature ou PBI.

Para localizar os comandos, digite `/` no campo de mensagem. Selecione o comando sugerido e complete a solicitação.

#### 4.5.7 Exportar uma conversa

1. Abra uma conversa já iniciada.
2. Selecione o botão de exportação no topo.
3. Aguarde a geração do PDF.

O botão fica desabilitado até que uma mensagem tenha criado uma conversa. Se não houver ID de conversa, a interface informa **Envie uma mensagem para exportar**.

---

### 4.7 Meu Perfil

Abra **Meu Perfil** no menu lateral para consultar:

- nome completo;
- e-mail;
- tipo de acesso;
- trajetória profissional vinculada ao mesmo e-mail;
- dados da sessão.

Se houver um registro profissional associado ao seu e-mail, a página mostra competências, participações em projetos e papéis. Se nenhum registro estiver vinculado, use a orientação exibida na tela para solicitar o cadastro a um administrador.

Na seção **Sessão**, selecione **Sair da conta** para encerrar o acesso. A plataforma volta para a tela de entrada depois de limpar a sessão.

---

### 4.8 Profissionais

A área **Profissionais** permite consultar o cadastro organizacional de profissionais e encontrar pessoas por competências.

#### 4.8.1 Cadastrar profissional

1. Selecione **Profissionais** no menu.
2. Selecione **Novo profissional**.
3. Informe nome, e-mail e selecione as competências relacionadas.
4. Confirme o cadastro.

O profissional aparece na listagem geral e pode ser localizado por meio da busca por competência.

#### 4.8.2 Buscar profissionais por competência

1. Selecione uma ou mais competências no painel **Buscar por competência**.
2. Selecione **Buscar**.
3. Consulte os resultados classificados por afinidade.

Cada resultado pode indicar:

- posição no ranking;
- percentual de afinidade;
- quantidade de competências correspondentes;
- competências já possuídas;
- competências que faltam;
- foco profissional no conjunto pesquisado.

Use **Limpar** para remover os critérios e retornar à listagem geral.

#### 4.8.3 Consultar trajetória profissional

Selecione o nome de um profissional para abrir seu perfil. A página pode mostrar:

- dados da pessoa;
- competências;
- participações em projetos;
- papéis exercidos;
- projetos gerenciáveis pelo usuário conectado;
- opções para alterar participações, conforme a permissão.

---

### 4.9 Competências

Na área **Competências**, é possível consultar o catálogo e verificar quais profissionais possuem cada item.

#### 4.9.1 Cadastrar competência

1. Selecione **Nova competência**.
2. Informe o nome.
3. Confirme o cadastro.

#### 4.9.2 Pesquisar e consultar

- Use **Filtrar competências** para localizar um nome no catálogo.
- Selecione uma competência para ver indicadores e profissionais classificados por afinidade.
- O catálogo mostra a quantidade de profissionais vinculados a cada competência.

#### 4.9.3 Renomear ou excluir

1. Use o lápis para renomear uma competência.
2. Administradores podem usar o botão da lixeira para excluir.
3. Leia a confirmação antes de excluir, pois a competência será removida do catálogo e dos profissionais vinculados.

---

### 4.10 Grafo de Conhecimento

O grafo representa entidades extraídas dos documentos e as relações entre elas.

#### 4.10.1 Grafo Global

Use **Grafo Global** para visualizar todas as entidades e relações disponíveis em todos os projetos.

#### 4.10.2 Grafo do projeto

Abra um projeto e expanda **Grafo de Conhecimento** para restringir a visualização àquele projeto.

O grafo pode estar vazio até que documentos sejam enviados e processados.

#### 4.10.3 Colorir por tipo ou comunidade

Use o controle **Tipo** ou **Comunidade**:

- **Tipo** colore os nós por categoria da entidade;
- **Comunidade** agrupa entidades em comunidades detectadas pelo GraphRAG.

A interface começa por comunidades quando existem pelo menos duas comunidades válidas. Caso contrário, começa por tipo.

#### 4.10.4 Buscar entidade

1. Digite o nome no campo **Buscar entidade**.
2. Selecione o botão de busca.
3. O nó correspondente fica destacado.

Use a busca para localizar nomes específicos em grafos grandes.

#### 4.10.5 Usar a legenda

A legenda mostra os tipos ou comunidades disponíveis.

- Selecione uma categoria para ocultar ou mostrar os nós correspondentes.
- Use **Mostrar tudo** para restaurar a visualização.
- Os nós ocultos não aparecem no grafo até serem exibidos novamente.

#### 4.10.6 Destacar nó e consultar relações

Selecione um nó para ver seu painel de detalhes. Passe o cursor sobre um nó para destacar suas relações imediatas.

Cada nó apresenta:

- nome;
- tipo;
- descrição;
- projeto;
- comunidade, quando disponível;
- grau de relacionamento;
- conexões com outros nós.

No painel de detalhes é possível navegar para nós relacionados.

#### 4.10.7 Controles do grafo

Os controles disponíveis podem incluir:

| Controle | Função |
| --- | --- |
| Zoom | Aproximar ou afastar a visualização. |
| Enquadrar | Ajustar todos os elementos visíveis ao tamanho da tela. |
| Reorganizar | Calcular novamente o posicionamento dos nós. |
| Tela cheia | Expandir o grafo para ocupar toda a tela. |
| Conexões entre grupos | Mostrar ou ocultar relações entre comunidades diferentes. |
| Mover comunidade junto | Ao arrastar um nó, mover também os nós da mesma comunidade. |

#### 4.10.8 Salvar posição dos nós

As posições dos nós podem ser salvas após arrastá-los. Essa organização é considerada uma preferência de visualização e pode ser restaurada ao recarregar o grafo.

Se o grafo estiver confuso:

1. Use **Reorganizar**.
2. Ative **Enquadrar**.
3. Filtre tipos ou comunidades pela legenda.
4. Use a busca para destacar uma entidade.

---

## 5. Perfil administrador

### 5.1 Acesso à Administração

Somente uma conta marcada como administradora pode abrir **Administração** no menu lateral. Se um usuário comum tentar abrir a rota diretamente, a aplicação redireciona para a Página Inicial.

### 5.2 Administração de logins

Na tela **Administração de logins**, o administrador pode:

- criar logins de PO;
- editar nome, e-mail e senha;
- localizar contas;
- filtrar contas ativas e desativadas;
- desativar uma conta;
- reativar uma conta;
- excluir um login;
- atualizar a lista.

O cadastro criado pela administração permite acesso como PO. Esta tela não concede nem remove o marcador de administrador em uma conta existente.

### 5.2.1 Criar um novo login

1. Selecione **Novo login** no topo da página.
2. Informe:
   - nome;
   - e-mail;
   - senha.
3. Confirme em **Cadastrar**.

A senha deve ter pelo menos oito caracteres. O nome e o e-mail são obrigatórios e devem usar valores válidos.

### 5.2.2 Editar um login

1. Localize a conta.
2. Selecione **Editar**.
3. Altere nome, e-mail ou senha.
4. Deixe o campo de nova senha em branco para manter a senha atual.
5. Selecione **Salvar**.

Ao alterar a senha, as sessões abertas daquele login são encerradas. O usuário precisará entrar novamente com a nova senha.

### 5.3 Localizar um login

1. Abra **Administração**.
2. Digite nome ou e-mail no campo de busca.
3. Use uma das opções:
   - **Todos**;
   - **Ativos**;
   - **Desativados**.
4. Os contadores indicam a quantidade em cada estado.

### 5.4 Desativar um login

1. Localize a conta ativa.
2. Selecione **Desativar**.
3. Leia o resumo da confirmação.
4. Selecione **Desativar** novamente.

O usuário perde a possibilidade de entrar e as sessões abertas são encerradas. Projetos e documentos não são excluídos pela desativação.

A conta própria não pode ser desativada pela própria tela.

### 5.5 Reativar um login

1. Selecione o filtro **Desativados**.
2. Localize a conta.
3. Selecione **Reativar**.
4. Confirme a ação.

Após a reativação, o usuário volta a conseguir entrar.

### 5.6 Excluir um login

1. Localize a conta.
2. Selecione **Excluir**.
3. Leia a descrição e confirme.

A exclusão remove o login da plataforma e impede sua reativação por esta interface. Os projetos e documentos associados são mantidos.

Tenha cuidado: confirme nome e e-mail antes de excluir. Como não há confirmação posterior para desfazer essa operação pela própria tela, use o recurso apenas quando necessário.

### 5.7 Atualizar a lista

Use o botão de atualização no topo para solicitar novamente os logins ao servidor. Enquanto a atualização acontece, a tela pode mostrar um indicador de carregamento.

## 6. Boas práticas

1. Use títulos objetivos e consistentes para projetos, documentos, épicos, Features e PBIs.
2. Mantenha descrições e regras no campo correto. Evite deixar informações críticas apenas em anexos.
3. Prefira `.txt` ou `.md` limpos, com seções e títulos identificáveis.
4. Aguarde o estado **Processado** antes de considerar um documento disponível para busca e chatbot.
5. Confira todas as fontes exibidas pelo assistente.
6. Revise sugestões de IA, validações e alertas de similaridade antes de aprová-las.
7. Não use o grafo como única fonte de decisão quando a entidade não tiver descrição ou relação suficiente.
8. Desative o acesso de um usuário em vez de excluir o login quando houver possibilidade de reativação futura.
9. Antes de excluir projeto ou login, confirme dependências e impactos com o responsável da área.
10. Ao registrar um problema, informe a tela, horário aproximado, ação realizada, mensagem exibida e identificação do projeto ou documento.

---

## 7. Perguntas frequentes e solução de problemas

### Não consigo entrar

- Confira o e-mail corporativo e a senha.
- Confirme se o usuário não está desativado.
- Limpe os cookies apenas se a equipe de suporte indicar.
- Se continuar sem acesso, solicite a criação ou reativação do login ao responsável pela plataforma.

### A página mostra “Você precisa fazer login”

A sessão expirou ou o navegador não tem mais o cookie de acesso. Entre novamente.

### A tela foi redirecionada ao login

Verifique se o token expirou ou se o administrador desativou o login.

### A lista de projetos não carrega

- Atualize a página.
- Confira sua conexão.
- Confira se o backend está disponível.
- Anote o horário e tente novamente.

### O documento foi rejeitado

Confirme:

- formato `.txt` ou `.md`;
- tamanho inferior ou igual a 10 MB;
- arquivo não corrompido;
- nome com extensão correta.

### O documento mostra “Erro”

1. Abra o menu do documento.
2. Selecione **Reprocessar**.
3. Aguarde a atualização.
4. Se o erro continuar, informe o projeto, o nome do arquivo e a mensagem exibida à equipe de suporte.

### A barra de envio está parada

Confirme a conexão de rede e aguarde a conclusão do serviço de IA. Arquivos grandes podem levar mais tempo. Não inicie vários envios simultâneos para o mesmo projeto.

### O chatbot não responde

- Confira se o serviço de IA está disponível.
- Tente enviar novamente em alguns segundos.
- Reduza o tamanho da pergunta.
- Confirme que os documentos necessários já foram processados.

### O chatbot respondeu algo incorreto ou incompleto

- Expanda as fontes.
- Confirme se o documento correto foi indexado.
- Verifique se o documento está **Processado**.
- Reformule a pergunta com mais contexto.
- Use `/validar` ou `/reformatar`, conforme necessário.

### O grafo não aparece

- Confirme que existem documentos processados no projeto.
- Aguarde a geração do grafo.
- Atualize a página.
- Recarregue a lista de documentos para verificar o estado.

