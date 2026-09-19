import { Epico } from "../types/api/epico";

export const epicos: Epico[] = [
    {
        id: 1,
        idProjeto: 1,
        titulo: "Digitalizar o acompanhamento de solicitações",
        descricao:
            "Criar uma experiência digital para que clientes acompanhem solicitações feitas à organização.",
        objetivo:
            "Reduzir dependência de contatos manuais e dar transparência ao andamento das solicitações.",
        escopoMacro: [
            "Consulta de solicitações",
            "Visualização de status",
            "Histórico de atualizações",
            "Notificações",
            "Tratamento de indisponibilidade",
        ],
        resultadoEsperado:
            "O cliente consegue acompanhar a evolução de suas solicitações por um canal digital sem depender de atendimento manual.",
        criteriosAceitacao: [
            "Os dados alterados em um canal devem permanecer consistentes nos demais canais suportados.",
            "O cliente deve conseguir identificar o status atual de qualquer solicitação sem intervenção humana.",
        ],
        createdAt: "2026-02-11T10:00:00.000Z",
    },
    {
        id: 2,
        idProjeto: 1,
        titulo: "Notificar clientes sobre mudanças de status",
        descricao:
            "Manter o cliente informado sobre atualizações relevantes de suas solicitações em tempo hábil.",
        objetivo:
            "Diminuir o volume de contatos reativos ao suporte perguntando sobre andamento.",
        escopoMacro: [
            "Notificações por e-mail",
            "Notificações no aplicativo",
            "Preferências de notificação",
        ],
        resultadoEsperado:
            "O cliente recebe avisos automáticos sempre que houver mudança relevante em uma solicitação.",
        criteriosAceitacao: [
            "Toda mudança de status deve gerar uma notificação em até 5 minutos.",
            "O cliente deve poder configurar quais canais de notificação deseja utilizar.",
        ],
        createdAt: "2026-02-18T14:20:00.000Z",
    },
    {
        id: 3,
        idProjeto: 2,
        titulo: "Padronizar a especificação de itens de trabalho",
        descricao:
            "Oferecer aos POs uma ferramenta guiada para especificar Épicos, Features e PBIs de forma consistente.",
        objetivo:
            "Reduzir retrabalho e ambiguidade entre produto, desenvolvimento e testes.",
        escopoMacro: [
            "Cadastro de Épicos",
            "Cadastro de Features",
            "Cadastro de PBIs",
            "Checklist de qualidade",
        ],
        resultadoEsperado:
            "POs conseguem criar itens de backlog completos e rastreáveis sem depender de templates externos.",
        criteriosAceitacao: [
            "Todo item criado deve conter os campos obrigatórios do seu nível.",
            "Deve ser possível rastrear a relação entre PBI, Feature e Épico.",
        ],
        createdAt: "2026-03-06T09:15:00.000Z",
    },
];