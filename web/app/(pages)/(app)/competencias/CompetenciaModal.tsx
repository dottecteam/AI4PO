"use client"

import { useEffect, useState, type FormEvent } from "react"
import {
  cadastrarCompetencia,
  renomearCompetencia,
} from "@/app/services/API/profissionais"
import { ApiError, encerrarSessao, mensagemDeErro, sessaoInvalida } from "@/app/services/API/usuarios"
import type { CompetenciaGerenciada } from "@/app/types/api/profissional"

// Mesmo limite do back (users/views_funcionarios.py)
const NOME_MAX = 150

type Props = {
  // Ausente = nova competência
  alvo?: CompetenciaGerenciada
  onFechar: () => void
  onSalvo: (competencia: CompetenciaGerenciada) => void
}

export default function CompetenciaModal({ alvo, onFechar, onSalvo }: Props) {
  const [nome, setNome] = useState(alvo?.nome ?? "")
  const [erro, setErro] = useState("")
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    const aoTeclar = (evento: KeyboardEvent) => {
      if (evento.key === "Escape" && !enviando) onFechar()
    }
    window.addEventListener("keydown", aoTeclar)
    return () => window.removeEventListener("keydown", aoTeclar)
  }, [enviando, onFechar])

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault()
    if (enviando) return

    const limpo = nome.trim().replace(/\s+/g, " ")
    if (!limpo) return setErro("Informe o nome da competência.")
    if (limpo.length > NOME_MAX) return setErro(`O nome pode ter no máximo ${NOME_MAX} caracteres.`)
    if (alvo && limpo === alvo.nome) return setErro("Nenhuma alteração para salvar.")

    setEnviando(true)
    setErro("")
    try {
      const salva = alvo ? await renomearCompetencia(alvo.id, limpo) : await cadastrarCompetencia(limpo)
      onSalvo(salva)
    } catch (e) {
      if (sessaoInvalida(e)) return encerrarSessao()
      setErro(e instanceof ApiError && e.campos.nome?.length ? e.campos.nome.join(" ") : mensagemDeErro(e))
      setEnviando(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <form
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-competencia"
        onSubmit={enviar}
        noValidate
        className="w-full max-w-md bg-(--surface-base) border border-gray-800/50 rounded-2xl p-6 flex flex-col gap-4 shadow-2xl"
      >
        <div className="flex flex-col gap-1">
          <h2 id="titulo-competencia" className="text-white text-lg font-semibold">
            {alvo ? "Renomear competência" : "Nova competência"}
          </h2>
          <p className="text-secondary text-sm">
            {alvo
              ? `${alvo.total_profissionais} profissional(is) passam a ver o novo nome.`
              : "Ela fica disponível no cadastro de profissionais e na busca por afinidade."}
          </p>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="competencia-nome" className="text-sm text-white">
            Nome
          </label>
          <input
            id="competencia-nome"
            type="text"
            autoFocus
            autoComplete="off"
            maxLength={NOME_MAX}
            placeholder="Ex.: Kubernetes"
            value={nome}
            onChange={(e) => {
              setNome(e.target.value)
              setErro("")
            }}
            aria-invalid={!!erro}
            className={`w-full h-11 bg-(--surface-elevated) outline-none rounded-xl px-4 text-sm text-white border transition duration-200 focus:ring-2 ${
              erro ? "border-red-500/60 focus:ring-red-500" : "border-gray-700/50 focus:ring-primary"
            }`}
          />
          {erro && (
            <p role="alert" className="text-xs text-red-300">
              {erro}
            </p>
          )}
        </div>

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
