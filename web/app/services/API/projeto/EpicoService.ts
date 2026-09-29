import { api } from "@/app/services/API/api";
import { Epico, EpicoInput } from "@/app/types/api/epico";

export const epicoService = {
    listar: () => api.get<Epico[]>("/api/epicos/"),

    listarPorProjeto: (idProjeto: number) =>
        api.get<Epico[]>(`/api/epicos/?idProjeto=${idProjeto}`),

    buscarPorId: (id: number) => api.get<Epico>(`/api/epicos/${id}/`),

    criar: (dados: EpicoInput) => api.post<Epico>("/api/epicos/", dados),

    editar: (id: number, dados: Partial<EpicoInput>) =>
        api.patch<Epico>(`/api/epicos/${id}/`, dados),

    excluir: (id: number) => api.delete<void>(`/api/epicos/${id}/`),
};