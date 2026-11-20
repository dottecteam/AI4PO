import { api } from "@/app/services/API/api"
import type { ParticipacaoInput, PerfilProfissional } from "@/app/types/api/profissional"

// Listagem, cadastro e busca por competência ficam em ./profissionais (Task #14)
export const profissionalService = {
  buscarPerfil: (id: number) => api.get<PerfilProfissional>(`/api/profissionais/${id}/`),

  // Perfil profissional do usuário logado (vinculado pelo e-mail).
  // A API responde 204 (sem corpo) quando não há profissional com esse e-mail.
  buscarMeuPerfil: async () =>
    (await api.get<PerfilProfissional | undefined>("/api/profissionais/me/")) ?? null,
}

// Registro de participação: criar/alterar/excluir só é permitido ao PO do
// projeto ou ao administrador (a API responde 403 nos demais casos).
export const participacaoService = {
  criar: (dados: ParticipacaoInput) => api.post<ParticipacaoInput & { id: number }>("/api/participacoes/", dados),

  editar: (id: number, dados: Partial<ParticipacaoInput>) =>
    api.patch<ParticipacaoInput & { id: number }>(`/api/participacoes/${id}/`, dados),

  excluir: (id: number) => api.delete<void>(`/api/participacoes/${id}/`),
}

// O helper `api` lança Error com o corpo JSON da resposta; extrai a mensagem legível.
export function mensagemDaApi(erro: unknown, padrao = "Não foi possível salvar as alterações.") {
  if (!(erro instanceof Error)) return padrao
  try {
    const corpo = JSON.parse(erro.message)
    if (typeof corpo?.detail === "string") return corpo.detail
    const primeira = Object.values(corpo ?? {}).flat().find((m) => typeof m === "string")
    return (primeira as string | undefined) ?? padrao
  } catch {
    return padrao
  }
}
