import type { ProjetoStatus } from "./projeto"

export interface Competencia {
  id: number
  nome: string
}

// Item da listagem de profissionais
export interface ProfissionalResumo {
  id: number
  nome: string
  email: string
  competencias: string[]
  total_projetos: number
}

// Participação do profissional em um projeto, com o papel desempenhado
export interface ParticipacaoPerfil {
  id: number
  papel: string
  criado_em: string
  projeto: {
    id: number
    titulo: string
    status: ProjetoStatus
  }
}

// Perfil completo: competências e trajetória em projetos
export interface PerfilProfissional {
  id: number
  nome: string
  email: string
  competencias: Competencia[]
  participacoes: ParticipacaoPerfil[]
}
