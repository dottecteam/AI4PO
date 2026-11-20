import { api } from "@/app/services/API/api"
import type { PerfilProfissional, ProfissionalResumo } from "@/app/types/api/profissional"

export const profissionalService = {
  listar: (busca = "") =>
    api.get<ProfissionalResumo[]>(
      `/api/profissionais/${busca.trim() ? `?busca=${encodeURIComponent(busca.trim())}` : ""}`,
    ),

  buscarPerfil: (id: number) => api.get<PerfilProfissional>(`/api/profissionais/${id}/`),

  // Perfil profissional do usuário logado (vinculado pelo e-mail).
  // A API responde 204 (sem corpo) quando não há profissional com esse e-mail.
  buscarMeuPerfil: async () =>
    (await api.get<PerfilProfissional | undefined>("/api/profissionais/me/")) ?? null,
}
