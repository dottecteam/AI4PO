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
  // O usuário logado é o PO do projeto ou administrador (Task #15-3)
  pode_editar: boolean
}

export interface ProjetoGerenciavel {
  id: number
  titulo: string
}

// Corpo de criação/edição de uma participação
export interface ParticipacaoInput {
  funcionario: number
  projeto: number
  papel: string
}

// Perfil completo: competências e trajetória em projetos
export interface PerfilProfissional {
  id: number
  nome: string
  email: string
  competencias: Competencia[]
  participacoes: ParticipacaoPerfil[]
  // Projetos em que o usuário logado pode registrar/alterar participações
  projetos_gerenciaveis: ProjetoGerenciavel[]
}
