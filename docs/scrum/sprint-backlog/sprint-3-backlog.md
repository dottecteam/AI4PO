# Backlog da Sprint 3

| ID | User Story | Definição de Pronto | Definição de Feito | Estimativa |
|:---:|:---|:---|:---|:---:|
| #11 | Como PO, desejo que o **Chatbot evolua para conversa em múltiplos turnos respeitando minhas permissões de acesso** para consultar o histórico de forma natural e segura. | - Chatbot básico entregue na Sprint 1;</br> - Regra de acesso a projetos definida;</br> - Comportamento de conversa aprovado pela equipe. | - Conversa mantendo contexto entre múltiplas perguntas;</br> - Respostas considerando apenas os documentos autorizados ao usuário;</br> - Fluxo validado pela equipe. |  |
| #12 | Como PO, desejo **receber sugestões automáticas de documentos e referências** ao pesquisar no Chatbot para encontrar material relevante. | - Busca por similaridade disponível na base vetorial;</br> - Layout das sugestões aprovado pela equipe. | - Documentos e referências relacionados exibidos junto à resposta;</br> - Documento sugerido acessível com um clique;</br> - Sugestões relevantes validadas pela equipe. |  |
| #13 | Como PO, desejo que o **Chatbot cite as fontes e requisitos originais** de onde retirou a resposta para auditabilidade da informação. | - Registro de origem das respostas definido;</br> - Comportamento das citações aprovado pela equipe. | - Toda resposta listando os documentos/projetos usados como fonte;</br> - Citações levando ao documento ou trecho original;</br> - Fonte indisponível informando a indisponibilidade. |  |
| #14 | Como gestor, desejo **buscar profissionais por competência prática** para montar equipes com maior afinidade técnica. | - Entidades de profissionais, participações e competências modeladas;</br> - Critérios de afinidade definidos pela equipe;</br> - Layout da tela de busca aprovado. | - Busca retornando profissionais ordenados por afinidade com os critérios utilizados;</br> - Ausência de afinidade informada listando os mais próximos;</br> - Fluxo validado pela equipe. |  |
| #15 | Como PO, desejo **ter minhas competências e projetos vinculados ao perfil** para mapear onde está o conhecimento técnico no time. | - Registro de participação definido (profissional, projeto, papel);</br> - Layout da tela de perfil aprovado pela equipe. | - Vínculo de profissional, projeto e papel funcionando;</br> - Duplicidade de registro alertada;</br> - Perfil exibindo a trajetória completa do profissional. |  |
| #16 | Como líder, desejo **ter acesso ao manual e à apresentação final** para operar a solução com autonomia. | - Todas as funcionalidades das sprints anteriores concluídas;</br> - Estrutura e público-alvo dos materiais definidos pela equipe. | - Manual publicado cobrindo os perfis PO e administrador;</br> - Apresentação final preparada e revisada;</br> - Linguagem acessível e validada pela equipe. |  |

---

## Tasks

| ID | Descrição | Definição de Pronto | Definição de Feito | Estimativa |
|:---:|:---|:---|:---|:---:|
| #11-6 | Adicionar suporte a múltiplos turnos com contexto de conversa na rota de pergunta/resposta. | - Chatbot básico entregue na Sprint 1. | - Endpoint mantendo o contexto da conversa entre perguntas do usuário. |  |
| #11-7 | Filtrar respostas do Chatbot pelos documentos autorizados ao usuário. | - Regra de acesso a projetos definida. | - Respostas considerando apenas os documentos permitidos ao usuário. |  |
| #11-8 | Realizar testes dos aprimoramentos do Chatbot. | - Aprimoramentos implementados. | - Cenários validados: contexto mantido em múltiplos turnos e permissões respeitadas. |  |
| #12-1 | Implementar busca de documentos relacionados por similaridade vetorial. | - Base vetorial disponível. | - Módulo retornando documentos relacionados à pergunta do usuário. |  |
| #12-2 | Exibir lista de documentos e referências sugeridas junto à resposta. | - Busca por similaridade funcional;</br> - Layout aprovado pela equipe. | - Sugestões visíveis junto a cada resposta do Chatbot. |  |
| #12-3 | Permitir abrir o documento sugerido a partir da lista. | - Sugestões exibidas na interface. | - Clique na sugestão abre o documento correspondente. |  |
| #12-4 | Realizar testes do fluxo de sugestões de documentos. | - Fluxo implementado. | - Cenários validados: sugestões relevantes à pergunta e abertura correta do documento. |  |
| #13-1 | Registrar na API os trechos e documentos usados em cada resposta. | - Recuperação semântica funcional. | - Cada resposta persistida com as fontes utilizadas. |  |
| #13-2 | Exibir citações clicáveis com link para o documento ou trecho original. | - Registro de fontes disponível;</br> - Layout aprovado pela equipe. | - Usuário consegue acessar a fonte original a partir da citação na resposta. |  |
| #13-3 | Tratar fonte removida ou sem permissão de acesso. | - Citações implementadas. | - Sistema informa a indisponibilidade da fonte sem quebrar a interface. |  |
| #13-4 | Realizar testes do fluxo de citação de fontes. | - Fluxo implementado. | - Cenários validados: toda resposta lista fontes e fonte indisponível informa erro. |  |
| #14-1 | Modelar entidades de profissionais, participações em projetos e competências no banco. | - Critérios de afinidade definidos pela equipe. | - Entidades criadas no banco e migrations executadas com sucesso. |  |
| #14-2 | Implementar rota de busca de profissionais por competência com ordenação por afinidade. | - Entidades modeladas. | - Endpoint retornando profissionais ordenados por afinidade com os critérios utilizados. |  |
| #14-3 | Implementar tela de busca e listagem de profissionais no frontend. | - Rota de busca disponível;</br> - Layout aprovado pela equipe. | - Gestor consegue buscar por competência e visualizar os resultados com os critérios de afinidade. |  |
| #14-4 | Realizar testes do fluxo de busca por competência. | - Fluxo implementado. | - Cenários validados: busca retorna ordenação correta e ausência de afinidade é informada. |  |
| #15-1 | Implementar registro de participação (profissional, projeto, papel) na API. | - Entidades de competências modeladas. | - Vínculo criado corretamente; duplicidade de registro alertada. |  |
| #15-2 | Implementar tela de perfil do profissional com projetos e competências. | - Registros de participação disponíveis;</br> - Layout aprovado pela equipe. | - Perfil exibindo projetos, papéis e competências do profissional. |  |
| #15-3 | Permitir atualização do registro pelo PO ou administrador. | - Registro implementado. | - Alterações persistidas corretamente respeitando o perfil do usuário. |  |
| #15-4 | Realizar testes do fluxo de vínculo de competências. | - Fluxo implementado. | - Cenários validados: vínculo registrado, duplicidade alertada e perfil exibindo a trajetória. |  |
| #16-1 | Elaborar manual do usuário cobrindo os perfis PO e administrador. | - Todas as funcionalidades estáveis e validadas. | - Manual publicado cobrindo todas as funcionalidades do sistema, com linguagem acessível. |  |
| #16-2 | Preparar apresentação final da solução. | - Manual em elaboração. | - Apresentação estruturada demonstrando o problema, a solução e os resultados. |  |
| #16-3 | Revisar e consolidar manual e apresentação com a equipe. | - Materiais produzidos. | - Materiais revisados, publicados e aprovados pela equipe. |  |
