import { Feature } from "../types/api/feature";

export const features: Feature[] = [
    {
        id: 1,
        idEpico: 1,
        titulo: "Consultar andamento de solicitações",
        descricao:
            "Permitir que o cliente visualize suas solicitações e identifique o estágio atual de cada uma.",
        objetivo:
            "Disponibilizar acompanhamento autônomo e reduzir dúvidas sobre andamento.",
        criteriosAceitacao: [
            "Listar somente solicitações autorizadas ao usuário",
            "Exibir status atual",
            "Permitir acesso ao histórico",
            "Tratar ausência de registros",
            "Informar indisponibilidade do serviço",
        ],
        createdAt: "2026-02-12T11:00:00.000Z",
    },
    {
        id: 2,
        idEpico: 1,
        titulo: "Exibir histórico de atualizações",
        descricao:
            "Permitir que o cliente visualize a linha do tempo de mudanças de uma solicitação específica.",
        objetivo:
            "Dar transparência sobre todas as etapas percorridas pela solicitação.",
        criteriosAceitacao: [
            "Ordenar eventos do mais recente para o mais antigo",
            "Exibir data e descrição de cada evento",
            "Tratar solicitações sem histórico registrado",
        ],
        createdAt: "2026-02-14T16:40:00.000Z",
    },
    {
        id: 3,
        idEpico: 2,
        titulo: "Configurar preferências de notificação",
        descricao:
            "Permitir que o cliente escolha por quais canais deseja ser notificado sobre mudanças de status.",
        objetivo:
            "Dar controle ao cliente sobre como e quando ser avisado.",
        criteriosAceitacao: [
            "Permitir ativar ou desativar e-mail e notificação no aplicativo",
            "Persistir a preferência entre sessões",
            "Aplicar a preferência a partir da próxima notificação gerada",
        ],
        createdAt: "2026-02-19T09:50:00.000Z",
    },
    {
        id: 4,
        idEpico: 3,
        titulo: "Cadastrar itens de backlog",
        descricao:
            "Permitir que o PO registre Épicos, Features e PBIs seguindo a estrutura obrigatória de cada nível.",
        objetivo:
            "Garantir que nenhum item seja criado sem os campos essenciais para rastreabilidade.",
        criteriosAceitacao: [
            "Impedir o salvamento de um item sem os campos obrigatórios do seu nível",
            "Vincular obrigatoriamente cada item ao seu item pai",
            "Exibir aviso quando um título de PBI não iniciar com verbo no infinitivo",
        ],
        createdAt: "2026-03-07T10:30:00.000Z",
    },
];