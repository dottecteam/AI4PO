import { PBI } from "../types/api/pbi";


export const pbis: PBI[] = [
    {
        id: 1,
        idFeature: 1,
        titulo: "Consultar solicitação",
        userStory: {
            como: "cliente autenticado",
            quero: "consultar os detalhes de uma solicitação",
            paraQue: "eu possa acompanhar sua situação atual",
        },
        cenarios: [
            {
                dado: "que o cliente possua uma solicitação acessível",
                quando: "selecionar a solicitação",
                entao: "o sistema deve apresentar seus dados e status atual",
            },
            {
                dado: "que a solicitação não pertença ao contexto permitido ao cliente",
                quando: "ele tentar acessá-la",
                entao: "o sistema deve impedir a consulta",
            },
        ],
        createdAt: "2026-02-13T09:10:00.000Z",
    },
    {
        id: 2,
        idFeature: 1,
        titulo: "Listar solicitações do cliente",
        userStory: {
            como: "cliente autenticado",
            quero: "visualizar a lista de todas as minhas solicitações",
            paraQue: "eu possa escolher qual delas consultar em detalhe",
        },
        regras: "A listagem deve ser paginada quando o cliente possuir mais de 20 solicitações.",
        cenarios: [
            {
                dado: "que o cliente possua ao menos uma solicitação registrada",
                quando: "acessar a tela de solicitações",
                entao: "o sistema deve exibir a lista com status resumido de cada uma",
            },
            {
                dado: "que o cliente não possua nenhuma solicitação registrada",
                quando: "acessar a tela de solicitações",
                entao: "o sistema deve exibir uma mensagem informando a ausência de registros",
            },
        ],
        createdAt: "2026-02-13T09:40:00.000Z",
    },
    {
        id: 3,
        idFeature: 2,
        titulo: "Exportar histórico de solicitação",
        userStory: {
            como: "cliente autenticado",
            quero: "exportar o histórico de uma solicitação em PDF",
            paraQue: "eu possa guardar um registro externo do andamento",
        },
        cenarios: [
            {
                dado: "que a solicitação possua histórico registrado",
                quando: "o cliente solicitar a exportação",
                entao: "o sistema deve gerar um arquivo PDF com os eventos em ordem cronológica",
            },
        ],
        createdAt: "2026-02-15T13:25:00.000Z",
    },
    {
        id: 4,
        idFeature: 3,
        titulo: "Atualizar preferência de notificação",
        userStory: {
            como: "cliente autenticado",
            quero: "escolher os canais pelos quais desejo ser notificado",
            paraQue: "eu receba avisos apenas pelos meios que prefiro usar",
        },
        cenarios: [
            {
                dado: "que o cliente esteja na tela de preferências",
                quando: "ele desmarcar um canal de notificação",
                entao: "o sistema deve deixar de enviar notificações por aquele canal",
            },
            {
                dado: "que o cliente não tenha selecionado nenhum canal",
                quando: "ele tentar salvar as preferências",
                entao: "o sistema deve impedir o salvamento e informar que ao menos um canal é obrigatório",
            },
        ],
        createdAt: "2026-02-20T15:05:00.000Z",
    },
    {
        id: 5,
        idFeature: 4,
        titulo: "Cadastrar Épico",
        userStory: {
            como: "PO",
            quero: "cadastrar um Épico com título, descrição, objetivo, escopo macro, resultado esperado e critérios de aceitação",
            paraQue: "eu registre a iniciativa de forma completa e rastreável",
        },
        regras: "O campo escopo macro deve aceitar múltiplos itens de texto.",
        cenarios: [
            {
                dado: "que o PO tenha preenchido todos os campos obrigatórios",
                quando: "ele salvar o Épico",
                entao: "o sistema deve criar o registro e vinculá-lo ao projeto atual",
            },
            {
                dado: "que o PO tenha deixado um campo obrigatório em branco",
                quando: "ele tentar salvar o Épico",
                entao: "o sistema deve impedir o salvamento e indicar o campo pendente",
            },
        ],
        createdAt: "2026-03-08T11:00:00.000Z",
    },
    {
        id: 6,
        idFeature: 4,
        titulo: "Cadastrar PBI",
        userStory: {
            como: "PO",
            quero: "cadastrar um PBI vinculado a uma Feature existente",
            paraQue: "eu detalhe um comportamento específico do sistema",
        },
        regras: "O título do PBI deve iniciar obrigatoriamente com verbo no infinitivo.",
        cenarios: [
            {
                dado: "que o título informado inicie com um verbo no infinitivo",
                quando: "o PO salvar o PBI",
                entao: "o sistema deve criar o registro vinculado à Feature selecionada",
            },
            {
                dado: "que o título informado não inicie com um verbo no infinitivo",
                quando: "o PO tentar salvar o PBI",
                entao: "o sistema deve impedir o salvamento e exibir um aviso sobre a convenção de título",
            },
        ],
        createdAt: "2026-03-08T11:20:00.000Z",
    },
];