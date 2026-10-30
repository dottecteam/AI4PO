import type { ErrosDeCampos, NovoLogin, UsuarioAdmin, UsuarioLogado } from "@/app/types/api/usuario"

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "")

export class ApiError extends Error {
  status: number
  campos: ErrosDeCampos

  constructor(status: number, message: string, campos: ErrosDeCampos = {}) {
    super(message)
    this.status = status
    this.campos = campos
  }
}

function lerCookie(nome: string) {
  if (typeof document === "undefined") return ""
  const par = document.cookie.split("; ").find((c) => c.startsWith(nome + "="))
  return par ? decodeURIComponent(par.split("=")[1]) : ""
}

async function requisitar<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  const metodo = (init.method ?? "GET").toUpperCase()
  const headers = new Headers(init.headers)
  if (init.body) headers.set("Content-Type", "application/json")
  if (metodo !== "GET") headers.set("X-CSRFToken", lerCookie("csrftoken"))

  const resposta = await fetch(`${API_URL}${caminho}`, {
    ...init,
    headers,
    credentials: "include",
  })

  if (!resposta.ok) {
    let detalhe = "Erro ao comunicar com o servidor."
    let campos: ErrosDeCampos = {}
    try {
      const corpo = await resposta.json()
      if (corpo?.detail) detalhe = corpo.detail
      if (corpo?.campos && typeof corpo.campos === "object") campos = corpo.campos
    } catch {
      // corpo sem JSON: mantém a mensagem padrão
    }
    throw new ApiError(resposta.status, detalhe, campos)
  }

  if (resposta.status === 204) return undefined as T
  return (await resposta.json()) as T
}

export const buscarUsuarioLogado = () => requisitar<UsuarioLogado>("/api/auth/me/")

export const listarUsuarios = () => requisitar<UsuarioAdmin[]>("/api/auth/admin/users/")

// Cadastra um novo PO
export const criarLogin = (dados: NovoLogin) =>
  requisitar<UsuarioAdmin>("/api/auth/admin/users/", {
    method: "POST",
    body: JSON.stringify(dados),
  })


export const alterarEstadoLogin = (id: number, isActive: boolean) =>
  requisitar<UsuarioAdmin>(`/api/auth/admin/users/${id}/`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  })

// o login deixa de existir para o usuário, mas projetos e documentos ficam
export const excluirLogin = (id: number) =>
  requisitar<void>(`/api/auth/admin/users/${id}/`, { method: "DELETE" })

export function mensagemDeErro(erro: unknown) {
  if (erro instanceof ApiError) return erro.message
  return "Não foi possível conectar ao servidor."
}

export function sessaoInvalida(erro: unknown) {
  return erro instanceof ApiError && erro.status === 401
}

export function encerrarSessao() {
  window.location.href = "/sair"
}