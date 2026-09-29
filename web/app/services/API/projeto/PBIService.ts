import { api } from "@/app/services/API/api";
import { PBI, PBIInput } from "@/app/types/api/pbi";

export const pbiService = {
    listar: () => api.get<PBI[]>("/api/pbis/"),

    listarPorFeature: (idFeature: number) =>
        api.get<PBI[]>(`/api/pbis/?idFeature=${idFeature}`),

    buscarPorId: (id: number) => api.get<PBI>(`/api/pbis/${id}/`),

    criar: (dados: PBIInput) => api.post<PBI>("/api/pbis/", dados),

    editar: (id: number, dados: Partial<PBIInput>) =>
        api.patch<PBI>(`/api/pbis/${id}/`, dados),

    excluir: (id: number) => api.delete<void>(`/api/pbis/${id}/`),
};