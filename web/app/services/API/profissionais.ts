import { requisitar } from "@/app/services/API/usuarios"
import type {
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