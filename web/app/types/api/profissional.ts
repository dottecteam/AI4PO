import type { ProjetoStatus } from "./projeto"

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

// Participação do profissional em um projeto, com o papel desempenhado (Task #15-2)
export type ParticipacaoPerfil = {
  id: number
  papel: string
  criado_em: string
  projeto: {
    id: number
    titulo: string
    status: ProjetoStatus
  }
  // O usuário logado é o PO do projeto ou administrador (Task #15-3)
  pode_editar: boolean
}

export type ProjetoGerenciavel = {
  id: number
  titulo: string
}

// Corpo de criação/edição de uma participação
export type ParticipacaoInput = {
  funcionario: number
  projeto: number
  papel: string
}

// Perfil completo: competências e trajetória em projetos
export type PerfilProfissional = {
  id: number
  nome: string
  email: string
  competencias: CompetenciaResumo[]
  participacoes: ParticipacaoPerfil[]
  // Projetos em que o usuário logado pode registrar/alterar participações
  projetos_gerenciaveis: ProjetoGerenciavel[]
}
