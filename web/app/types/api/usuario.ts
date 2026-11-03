// Usuário logado
export type UsuarioLogado = {
  id: number
  nome: string
  email: string
  is_admin: boolean
}

// Corpo do cadastro de PO
export type NovoLogin = {
  nome: string
  email: string
  senha: string
}

export type ErrosDeCampos = Partial<Record<keyof NovoLogin, string[]>>

// Login de PO nas rotas administrativas
export type UsuarioAdmin = {
  id: number
  nome: string
  email: string
  is_active: boolean
  is_admin: boolean
  excluido_em: string | null
}