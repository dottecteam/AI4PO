export type CompetenciaResumo = {
  id: number
  nome: string
}

export type Profissional = {
  id: number
  nome: string
  email: string
  competencias: CompetenciaResumo[]
}

export type NovoProfissional = {
  nome: string
  email: string
  competencias: number[]
}

export type ProfissionalAfinidade = {
  id: number
  nome: string
  email: string
  afinidade: number
  competencias_correspondentes: CompetenciaResumo[]
  competencias_faltantes: CompetenciaResumo[]
  total_competencias: number
  foco: number
}

export type CriteriosBusca = {
  competencias_buscadas: CompetenciaResumo[]
  afinidade: string
  ordenacao: string[]
}

export type ResultadoBusca = {
  criterios: CriteriosBusca
  total: number
  resultados: ProfissionalAfinidade[]
}