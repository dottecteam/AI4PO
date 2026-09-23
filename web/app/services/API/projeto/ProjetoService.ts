import { api } from "@/app/services/API/api";
import { Projeto, ProjetoInput } from "@/app/types/api/projeto";

export const projetoService = {
    listar: () => api.get<Projeto[]>("/api/projetos/"),

    buscarPorId: (id: number) => api.get<Projeto>(`/api/projetos/${id}/`),

    criar: (dados: ProjetoInput) => api.post<Projeto>("/api/projetos/", dados),

    editar: (id: number, dados: Partial<ProjetoInput>) =>
        api.patch<Projeto>(`/api/projetos/${id}/`, dados),

    excluir: (id: number) => api.delete<void>(`/api/projetos/${id}/`),
};