import { Projeto } from "../types/api/projeto";

export const projetos: Projeto[] = [
    {
        id: 1,
        titulo: "Portal de Acompanhamento de Solicitações",
        descricao:
            "Plataforma digital para que clientes acompanhem o andamento de solicitações feitas à organização, sem depender de atendimento manual.",
        status: "Ativo",
        po: "Marina Alves",
        createdAt: "2026-02-10T09:00:00.000Z",
    },
    {
        id: 2,
        titulo: "Sistema de Gestão de Backlog para POs",
        descricao:
            "Ferramenta interna para padronizar a especificação de Épicos, Features e PBIs entre times de produto.",
        status: "Rascunho",
        po: "Rafael Souza",
        createdAt: "2026-03-05T13:45:00.000Z",
    },
    {
        id: 3,
        titulo: "App de Onboarding de Colaboradores",
        descricao:
            "Aplicativo para centralizar o processo de admissão e integração de novos funcionários.",
        status: "Inativo",
        po: "Camila Torres",
        createdAt: "2025-11-20T08:30:00.000Z",
    },
];