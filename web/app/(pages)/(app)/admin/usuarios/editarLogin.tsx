"use client"

import { useEffect, useState, type FormEvent } from "react"
import { Eye, EyeOff } from "lucide-react"
import {
  ApiError,
  editarLogin,
  encerrarSessao,
  mensagemDeErro,
  sessaoInvalida,
} from "@/app/services/API/usuarios"
import type { ErrosDeCampos, NovoLogin, UsuarioAdmin } from "@/app/types/api/usuario"

// Mesmos limites do back (api/users/views.py)
const NOME_MAX = 100
const EMAIL_MAX = 254
const SENHA_MIN = 8
const EMAIL_VALIDO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

type Campo = keyof NovoLogin
type Erros = Partial<Record<Campo, string>>

// A senha é opcional na edição: em branco significa "manter a atual"
function validar({ nome, email, senha }: NovoLogin): Erros {
  const erros: Erros = {}

  if (!nome.trim()) erros.nome = "O nome é obrigatório."
  else if (nome.trim().length > NOME_MAX) erros.nome = `O nome pode ter no máximo ${NOME_MAX} caracteres.`

  if (!email.trim()) erros.email = "O e-mail é obrigatório."
  else if (email.trim().length > EMAIL_MAX) erros.email = `O e-mail pode ter no máximo ${EMAIL_MAX} caracteres.`
  else if (!EMAIL_VALIDO.test(email.trim())) erros.email = "Informe um e-mail válido."

  if (senha && senha.length < SENHA_MIN) erros.senha = `A senha deve ter pelo menos ${SENHA_MIN} caracteres.`

  return erros
}

function errosDoServidor(campos: ErrosDeCampos): Erros {
  const erros: Erros = {}
  for (const campo of ["nome", "email", "senha"] as Campo[]) {
    const mensagens = campos[campo]
    if (mensagens?.length) erros[campo] = mensagens.join(" ")
  }
  return erros
}

type Props = {
  alvo: UsuarioAdmin
  onFechar: () => void
  onSalvo: (usuario: UsuarioAdmin) => void
}

export default function EditarLoginModal({ alvo, onFechar, onSalvo }: Props) {
  const [valores, setValores] = useState<NovoLogin>({ nome: alvo.nome, email: alvo.email, senha: "" })
  const [erros, setErros] = useState<Erros>({})
  const [erroGeral, setErroGeral] = useState("")
  const [enviando, setEnviando] = useState(false)
  const [mostrarSenha, setMostrarSenha] = useState(false)

  // Esc fecha (a menos que o salvamento esteja em andamento)
  useEffect(() => {
    const aoTeclar = (evento: KeyboardEvent) => {
      if (evento.key === "Escape" && !enviando) onFechar()
    }
    window.addEventListener("keydown", aoTeclar)
    return () => window.removeEventListener("keydown", aoTeclar)
  }, [enviando, onFechar])

  const alterar = (campo: Campo, valor: string) => {
    setValores((prev) => ({ ...prev, [campo]: valor }))
    setErros((prev) => ({ ...prev, [campo]: undefined }))
    setErroGeral("")
  }

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault()
    if (enviando) return

    const encontrados = validar(valores)
    if (Object.keys(encontrados).length > 0) {
      setErros(encontrados)
      return
    }

    // Só manda o que mudou
    const mudancas: Partial<NovoLogin> = {}
    if (valores.nome.trim() !== alvo.nome) mudancas.nome = valores.nome.trim()
    if (valores.email.trim().toLowerCase() !== alvo.email.toLowerCase()) mudancas.email = valores.email.trim()
    if (valores.senha) mudancas.senha = valores.senha

    if (Object.keys(mudancas).length === 0) {
      setErroGeral("Nenhuma alteração para salvar.")
      return
    }

    setEnviando(true)
    setErroGeral("")
    try {
      const salvo = await editarLogin(alvo.id, mudancas)
      onSalvo(salvo)
    } catch (e) {
      if (sessaoInvalida(e)) {
        encerrarSessao()
        return
      }
      if (e instanceof ApiError && e.status === 400 && Object.keys(e.campos).length > 0) {
        setErros(errosDoServidor(e.campos))
      } else {
        setErroGeral(mensagemDeErro(e))
      }
    } finally {
      setEnviando(false)
    }
  }

  const classeInput = (campo: Campo) =>
    `w-full h-11 bg-(--surface-elevated) outline-none rounded-xl px-4 text-sm text-white border transition duration-200 focus:ring-2 ${
      erros[campo] ? "border-red-500/60 focus:ring-red-500" : "border-gray-700/50 focus:ring-primary"
    }`

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <form
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-editar-login"
        onSubmit={enviar}
        noValidate
        className="w-full max-w-md bg-(--surface-base) border border-gray-800/50 rounded-2xl p-6 flex flex-col gap-4 shadow-2xl"
      >
        <div className="flex flex-col gap-1">
          <h2 id="titulo-editar-login" className="text-white text-lg font-semibold">
            Editar login
          </h2>
          <p className="text-secondary text-sm">
            Altere os dados de {alvo.nome}. Os projetos e documentos continuam os mesmos.
          </p>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="editar-nome" className="text-sm text-white">
            Nome
          </label>
          <input
            id="editar-nome"
            type="text"
            autoFocus
            autoComplete="off"
            value={valores.nome}
            onChange={(e) => alterar("nome", e.target.value)}
            aria-invalid={!!erros.nome}
            aria-describedby={erros.nome ? "erro-editar-nome" : undefined}
            className={classeInput("nome")}
          />
          {erros.nome && (
            <p id="erro-editar-nome" className="text-xs text-red-300">
              {erros.nome}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="editar-email" className="text-sm text-white">
            E-mail
          </label>
          <input
            id="editar-email"
            type="email"
            autoComplete="off"
            value={valores.email}
            onChange={(e) => alterar("email", e.target.value)}
            aria-invalid={!!erros.email}
            aria-describedby={erros.email ? "erro-editar-email" : undefined}
            className={classeInput("email")}
          />
          {erros.email && (
            <p id="erro-editar-email" className="text-xs text-red-300">
              {erros.email}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="editar-senha" className="text-sm text-white">
            Nova senha (opcional)
          </label>
          <div className="relative">
            <input
              id="editar-senha"
              type={mostrarSenha ? "text" : "password"}
              autoComplete="new-password"
              value={valores.senha}
              onChange={(e) => alterar("senha", e.target.value)}
              aria-invalid={!!erros.senha}
              aria-describedby={erros.senha ? "erro-editar-senha" : "ajuda-editar-senha"}
              className={`${classeInput("senha")} pr-11`}
            />
            <button
              type="button"
              onClick={() => setMostrarSenha((v) => !v)}
              aria-label={mostrarSenha ? "Ocultar senha" : "Mostrar senha"}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary hover:text-white"
            >
              {mostrarSenha ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {erros.senha ? (
            <p id="erro-editar-senha" className="text-xs text-red-300">
              {erros.senha}
            </p>
          ) : (
            <p id="ajuda-editar-senha" className="text-xs text-secondary">
              Deixe em branco para manter a atual. Ao trocar, as sessões abertas desse login são encerradas.
            </p>
          )}
        </div>

        {erroGeral && (
          <p role="alert" className="text-sm text-red-300">
            {erroGeral}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onFechar}
            disabled={enviando}
            className="h-10 px-4 rounded-lg text-sm text-white border border-gray-700/50 hover:bg-(--surface-elevated) transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={enviando}
            className="h-10 px-4 rounded-lg text-sm font-medium text-white bg-primary hover:bg-primary-dark transition-colors disabled:opacity-50"
          >
            {enviando ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>
    </div>
  )
}