// Usuário logado
export type UsuarioLogado = {
  id: number
  nome: string
  email: string
  is_admin: boolean
}

// Login de PO
export type UsuarioAdmin = {
  id: number
  nome: string
  email: string
  is_active: boolean
  is_admin: boolean
  excluido_em: string | null
}