import { requisitar } from "@/app/services/API/usuarios"
import type {
  CompetenciaGerenciada,
  CompetenciaResumo,
  NovoProfissional,
  Profissional,
  ResultadoBusca,
} from "@/app/types/api/profissional"

export const listarCompetencias = () => requisitar<CompetenciaResumo[]>("/api/competencias/")

export const listarProfissionais = () => requisitar<Profissional[]>("/api/profissionais/")

export const buscarProfissionais = (competencias: number[]) =>
  requisitar<ResultadoBusca>(`/api/profissionais/busca/?competencias=${competencias.join(",")}`)

export const cadastrarProfissional = (dados: NovoProfissional) =>
  requisitar<Profissional>("/api/profissionais/", {
    method: "POST",
    body: JSON.stringify(dados),
  })

// Gerenciamento de competências
export const listarCompetenciasComTotais = () =>
  requisitar<CompetenciaGerenciada[]>("/api/competencias/?com_totais=1")

export const cadastrarCompetencia = (nome: string) =>
  requisitar<CompetenciaGerenciada>("/api/competencias/", {
    method: "POST",
    body: JSON.stringify({ nome }),
  })

export const renomearCompetencia = (id: number, nome: string) =>
  requisitar<CompetenciaGerenciada>(`/api/competencias/${id}/`, {
    method: "PATCH",
    body: JSON.stringify({ nome }),
  })

// Somente administrador; remove a competência de todos os profissionais
export const excluirCompetencia = (id: number) =>
  requisitar<void>(`/api/competencias/${id}/`, { method: "DELETE" })
