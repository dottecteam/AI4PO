import { Projeto } from "../types/api/projetos";

export const projetos: Projeto[] = [
    {
        id: "projetos-001",
        titulo: "Estrutura de Webhooks Idempotentes",
        descricao: "Descrição Lorem ipsum dolor sit amet consectetur adipisicing elit.Officia enim optio, dolorem quas harum quae doloremque saepe, illo cum voluptas, quibusdam corporis molestiae veniam animi dolor amet fuga! Error, quis.Lorem ipsum, dolor sit amet consectetur adipisicing elit.Laboriosam odio vitae minima! Excepturi quisquam neque ad nostrum tempora nihil quae quis officiis ipsam? Recusandae quas ab incidunt sint consectetur aut! Lorem ipsum dolor sit amet consectetur adipisicing elit.Consectetur hic tempora suscipit beatae sapiente consequatur cum id obcaecati fugit voluptatibus.Adipisci, officia.Ea harum voluptate iste omnis rerum dignissimos.Veritatis.",
        objetivo: "Objetivo Lorem ipsum dolor sit amet consectetur adipisicing elit. Officia enim optio, dolorem quas harum quae doloremque saepe, illo cum voluptas, quibusdam corporis molestiae veniam animi dolor amet fuga! Error, quis. Lorem ipsum, dolor sit amet consectetur adipisicing elit. Laboriosam odio vitae minima! Excepturi quisquam neque ad nostrum tempora nihil quae quis officiis ipsam? Recusandae quas ab incidunt sint consectetur aut! Lorem ipsum dolor sit amet consectetur adipisicing elit. Consectetur hic tempora suscipit beatae sapiente consequatur cum id obcaecati fugit voluptatibus. Adipisci, officia. Ea harum voluptate iste omnis rerum dignissimos. Veritatis.",
        setor: "PayCore V3",
        status: "Rascunho",
        po: "Thiago Silva",
        createdAt: "2026-02-12",

        epicos: [
            {
                id: "epic-001",
                titulo: "Digitalizar o acompanhamento de solicitações",

                descricao:
                    "Criar uma experiência digital para que clientes acompanhem solicitações feitas à organização.",

                objetivo:
                    "Reduzir a dependência de contatos manuais e dar transparência ao andamento das solicitações.",

                escopoMacro: [
                    "Consulta de solicitações",
                    "Visualização de status",
                    "Histórico de atualizações",
                    "Notificações",
                    "Tratamento de indisponibilidade",
                ],

                resultadoEsperado:
                    "O cliente consegue acompanhar a evolução de suas solicitações por um canal digital sem depender de atendimento manual.",

                criterioDeAceitacao: [
                    "Os dados alterados em um canal permanecem consistentes nos demais canais suportados.",
                    "O cliente consegue consultar o andamento de suas solicitações.",
                    "O sistema mantém o histórico das atualizações.",
                ],

                features: [
                    {
                        id: "feature-001",

                        titulo: "Consultar andamento de solicitações",

                        descricao:
                            "Permitir que o cliente visualize suas solicitações e identifique o estágio atual de cada uma.",

                        objetivo:
                            "Disponibilizar acompanhamento autônomo e reduzir dúvidas sobre andamento.",

                        criterioDeAceitacao: [
                            "Listar somente solicitações autorizadas ao usuário.",
                            "Exibir o status atual da solicitação.",
                            "Permitir acesso ao histórico.",
                            "Tratar ausência de registros.",
                            "Informar indisponibilidade do serviço.",
                        ],

                        pbis: [
                            {
                                id: "pbi-001",

                                titulo: "Consultar solicitação",

                                userStory: {
                                    como: "cliente autenticado",
                                    quero: "consultar os detalhes de uma solicitação",
                                    paraQue: "possa acompanhar sua situação atual",
                                },

                                prototipo: "/prototypes/consultar-solicitacao",

                                cenarios: [
                                    {
                                        id: "scenario-001",
                                        titulo: "Exibir os detalhes",
                                        dado: "que o cliente possua uma solicitação acessível",
                                        quando: "selecionar a solicitação",
                                        entao: "o sistema deve apresentar seus dados e status atual",
                                    },
                                    {
                                        id: "scenario-002",
                                        titulo: "Impedir acesso não autorizado",
                                        dado:
                                            "que a solicitação não pertença ao contexto permitido ao cliente",
                                        quando: "ele tentar acessá-la",
                                        entao: "o sistema deve impedir a consulta",
                                    },
                                ],

                                regras: [
                                    "O usuário só pode consultar solicitações às quais possui acesso.",
                                ],
                            },

                            {
                                id: "pbi-002",

                                titulo: "Filtrar solicitações",

                                userStory: {
                                    como: "cliente autenticado",
                                    quero: "filtrar minhas solicitações",
                                    paraQue: "possa localizar uma solicitação específica",
                                },

                                cenarios: [
                                    {
                                        id: "scenario-003",
                                        titulo: "Filtrar por status",
                                        dado: "que existam solicitações cadastradas",
                                        quando: "selecionar um status para filtragem",
                                        entao: "o sistema deve apresentar somente solicitações daquele status",
                                    },
                                    {
                                        id: "scenario-004",
                                        titulo: "Nenhum resultado",
                                        dado: "que não existam solicitações correspondentes ao filtro",
                                        quando: "aplicar o filtro",
                                        entao: "o sistema deve informar que nenhum registro foi encontrado",
                                    },
                                ],
                            },
                        ],
                    },
                ],

                createdAt: "21/03/2025",
            },

            {
                id: "epic-002",

                titulo: "Gerenciar notificações",

                descricao:
                    "Disponibilizar mecanismos para informar o usuário sobre alterações relevantes nas suas solicitações.",

                objetivo:
                    "Manter o usuário informado sobre mudanças no andamento das solicitações.",

                escopoMacro: [
                    "Notificações de atualização",
                    "Visualização de notificações",
                    "Controle de notificações",
                ],

                resultadoEsperado:
                    "O usuário recebe e consulta notificações relacionadas às suas solicitações.",

                criterioDeAceitacao: [
                    "Notificações devem estar relacionadas a eventos relevantes.",
                    "O usuário deve visualizar notificações às quais possui acesso.",
                ],

                features: [
                    {
                        id: "feature-002",

                        titulo: "Receber notificações de solicitações",

                        descricao:
                            "Permitir que o usuário seja informado quando ocorrerem alterações relevantes em suas solicitações.",

                        objetivo:
                            "Reduzir a necessidade de consultas manuais ao sistema.",

                        criterioDeAceitacao: [
                            "Gerar notificação quando ocorrer um evento configurado.",
                            "Relacionar a notificação à solicitação correspondente.",
                        ],

                        pbis: [
                            {
                                id: "pbi-003",

                                titulo: "Visualizar notificações",

                                userStory: {
                                    como: "cliente autenticado",
                                    quero: "visualizar minhas notificações",
                                    paraQue: "possa identificar alterações nas minhas solicitações",
                                },

                                cenarios: [
                                    {
                                        id: "scenario-005",
                                        titulo: "Exibir notificações",
                                        dado: "que existam notificações para o usuário",
                                        quando: "acessar a área de notificações",
                                        entao: "o sistema deve apresentar as notificações disponíveis",
                                    },
                                ],
                            },
                        ],
                    },
                ],

                createdAt: "21/03/2025",
            },
        ],
    },
];