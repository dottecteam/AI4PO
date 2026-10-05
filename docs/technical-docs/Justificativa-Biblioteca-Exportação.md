**Justificativa:** uso do WeasyPrint para exportação de conversas em PDF

A exportação das conversas do assistente em PDF será implementada no backend, com a **biblioteca WeasyPrint**, a partir do conteúdo persistido no banco de dados. Essa escolha se baseia nos seguintes pontos:

1. Aderência ao formato do conteúdo. As respostas do agente são produzidas em Markdown, que é convertido para HTML. O WeasyPrint transforma HTML e CSS diretamente em PDF, então títulos, listas, tabelas e blocos de código são preservados sem que o layout precise ser montado manualmente em código, como seria com o ReportLab.

2. Qualidade do documento gerado. O PDF é construído a partir do texto das mensagens, e não da captura da tela. Com isso, o texto permanece selecionável e pesquisável, o arquivo é leve e a quebra de páginas é automática, mesmo em conversas longas. Soluções baseadas em captura de tela (como jsPDF com html2canvas) geram imagens, perdem essas características e dependem do que o usuário tem carregado no navegador.

3. Consistência e segurança. Gerar o arquivo no servidor garante que o PDF reflita sempre o histórico completo salvo, independentemente do estado do cliente. A autorização reaproveita o controle de acesso já existente (autenticação por cookie JWT e filtro por usuário proprietário da conversa), sem expor dados adicionais ao front-end.

4. Integração com a stack. A biblioteca é Python e se integra à view Django sem alterar a arquitetura. A estilização via CSS permite manter a identidade visual da Pro4Tech no documento com baixo esforço, e a mesma função de geração pode ser reutilizada para exportar uma única resposta do agente.

5. Custo e manutenção. O WeasyPrint é open source, ativamente mantido e tem licença permissiva (BSD). O volume esperado (uma ação pontual do usuário, sobre conversas de dezenas de mensagens) é compatível com o tempo de renderização da biblioteca.

**Riscos e mitigações.** A biblioteca depende de bibliotecas de sistema (Pango), o que exige adicioná-las ao Dockerfile e documentar a instalação para execução fora do Docker. Além disso, como o conteúdo vem do usuário e do modelo, o HTML deve ser sanitizado antes da renderização para evitar injeção de tags e requisições indevidas a recursos externos.

**Alternativa considerada.** O ReportLab dispensa dependências de sistema, mas exige construir manualmente o layout e converter o Markdown, o que aumenta o código a manter. Ele permanece como plano B caso a instalação das dependências do WeasyPrint se mostre um impedimento para a equipe.
