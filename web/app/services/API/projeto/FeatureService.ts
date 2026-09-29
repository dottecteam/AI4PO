import { api } from "@/app/services/API/api";
import { Feature, FeatureInput } from "@/app/types/api/feature";

export const featureService = {
    listar: () => api.get<Feature[]>("/api/features/"),

    listarPorEpico: (idEpico: number) =>
        api.get<Feature[]>(`/api/features/?idEpico=${idEpico}`),

    buscarPorId: (id: number) => api.get<Feature>(`/api/features/${id}/`),

    criar: (dados: FeatureInput) => api.post<Feature>("/api/features/", dados),

    editar: (id: number, dados: Partial<FeatureInput>) =>
        api.patch<Feature>(`/api/features/${id}/`, dados),

    excluir: (id: number) => api.delete<void>(`/api/features/${id}/`),
};