"use client"

import { useEffect, useState, type FormEvent } from "react"
import { ApiError, encerrarSessao, mensagemDeErro, sessaoInvalida } from "@/app/services/API/usuarios"
import { cadastrarProfissional } from "@/app/services/API/profissionais"
import type { ErrosDeCampos } from "@/app/types/api/usuario"
import type { CompetenciaResumo, NovoProfissional, Profissional } from "@/app/types/api/profissional"
import SeletorCompetencias from "./SeletorCompetencias"

const NOME_MAX = 255
const EMAIL_MAX = 254
const EMAIL_VALIDO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

type Campo = keyof NovoProfissional
type Erros = Partial<Record<Campo, string>>

function validar({ nome, email, competencias }: NovoProfissional): Erros {
  const erros: Erros = {}

  if (!nome.trim()) erros.nome = "O nome é obrigatório."
  else if (nome.trim().length > NOME_MAX) erros.nome = `O nome pode ter no máximo ${NOME_MAX} caracteres.`

  if (!email.trim()) erros.email = "O e-mail é obrigatório."
  else if (email.trim().length > EMAIL_MAX) erros.email = `O e-mail pode ter no máximo ${EMAIL_MAX} caracteres.`
  else if (!EMAIL_VALIDO.test(email.trim())) erros.email = "Informe um e-mail válido."

  if (competencias.length === 0) erros.competencias = "Selecione ao menos uma competência."

  return erros
}

function errosDoServidor(campos: ErrosDeCampos): Erros {
  const erros: Erros = {}
  for (const campo of ["nome", "email", "competencias"] as Campo[]) {
    const mensagens = campos[campo]
    if (mensagens?.length) erros[campo] = mensagens.join(" ")
  }
  return erros
}

type Props = {
  competencias: CompetenciaResumo[]
  onFechar: () => void
  onCriado: (profissional: Profissional) => void
}

export default function CadastroProfissionalModal({ competencias, onFechar, onCriado }: Props) {
  const [valores, setValores] = useState<NovoProfissional>({ nome: "", email: "", competencias: [] })
  const [erros, setErros] = useState<Erros>({})
  const [erroGeral, setErroGeral] = useState("")
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    const aoTeclar = (evento: KeyboardEvent) => {
      if (evento.key === "Escape" && !enviando) onFechar()
    }
    window.addEventListener("keydown", aoTeclar)
    return () => window.removeEventListener("keydown", aoTeclar)
  }, [enviando, onFechar])

  const alterar = <C extends Campo>(campo: C, valor: NovoProfissional[C]) => {
    setValores((prev) => ({ ...prev, [campo]: valor }))
    // Quem está corrigindo o campo não precisa ver o erro antigo
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

    setEnviando(true)
    setErroGeral("")
    try {
      const criado = await cadastrarProfissional({
        nome: valores.nome.trim(),
        email: valores.email.trim(),
        competencias: valores.competencias,
      })
      onCriado(criado)
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

  const semCatalogo = competencias.length === 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <form
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-novo-profissional"
        onSubmit={enviar}
        noValidate
        className="w-full max-w-lg max-h-[90vh] overflow-y-auto bg-(--surface-base) border border-gray-800/50 rounded-2xl p-6 flex flex-col gap-4 shadow-2xl"
      >
        <div className="flex flex-col gap-1">
          <h2 id="titulo-novo-profissional" className="text-white text-lg font-semibold">
            Novo profissional
          </h2>
          <p className="text-secondary text-sm">
            As competências escolhidas é que fazem o profissional aparecer nas buscas.
          </p>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="prof-nome" className="text-sm text-white">
            Nome
          </label>
          <input
            id="prof-nome"
            type="text"
            autoFocus
            autoComplete="off"
            value={valores.nome}
            onChange={(e) => alterar("nome", e.target.value)}
            aria-invalid={!!erros.nome}
            aria-describedby={erros.nome ? "erro-prof-nome" : undefined}
            className={classeInput("nome")}
          />
          {erros.nome && (
            <p id="erro-prof-nome" className="text-xs text-red-300">
              {erros.nome}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="prof-email" className="text-sm text-white">
            E-mail
          </label>
          <input
            id="prof-email"
            type="email"
            autoComplete="off"
            value={valores.email}
            onChange={(e) => alterar("email", e.target.value)}
            aria-invalid={!!erros.email}
            aria-describedby={erros.email ? "erro-prof-email" : undefined}
            className={classeInput("email")}
          />
          {erros.email && (
            <p id="erro-prof-email" className="text-xs text-red-300">
              {erros.email}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <span id="rotulo-prof-competencias" className="text-sm text-white">
            Competências
          </span>
          {semCatalogo ? (
            <p className="text-sm text-secondary">
              Ainda não há competências cadastradas, então não é possível cadastrar profissionais.
            </p>
          ) : (
            <SeletorCompetencias
              rotulo="Competências do profissional"
              competencias={competencias}
              selecionadas={valores.competencias}
              onAlterar={(ids) => alterar("competencias", ids)}
              desabilitado={enviando}
              descritoPor={erros.competencias ? "erro-prof-competencias" : undefined}
            />
          )}
          {erros.competencias && (
            <p id="erro-prof-competencias" className="text-xs text-red-300">
              {erros.competencias}
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
            disabled={enviando || semCatalogo}
            className="h-10 px-4 rounded-lg text-sm font-medium text-white bg-primary hover:bg-primary-dark transition-colors disabled:opacity-50"
          >
            {enviando ? "Cadastrando..." : "Cadastrar"}
          </button>
        </div>
      </form>
    </div>
  )
}