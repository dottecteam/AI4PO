"use client"

import { useMemo, useState } from "react"
import { Search } from "lucide-react"
import type { CompetenciaResumo } from "@/app/types/api/profissional"

const LIMITE_SEM_FILTRO = 8

type Props = {
  rotulo: string
  competencias: CompetenciaResumo[]
  selecionadas: number[]
  onAlterar: (ids: number[]) => void
  desabilitado?: boolean
  descritoPor?: string 
}

export default function SeletorCompetencias({
  rotulo,
  competencias,
  selecionadas,
  onAlterar,
  desabilitado = false,
  descritoPor,
}: Props) {
  const [filtro, setFiltro] = useState("")

  const visiveis = useMemo(() => {
    const termo = filtro.trim().toLowerCase()
    if (!termo) return competencias
    return competencias.filter((c) => c.nome.toLowerCase().includes(termo))
  }, [competencias, filtro])

  const alternar = (id: number) => {
    onAlterar(selecionadas.includes(id) ? selecionadas.filter((s) => s !== id) : [...selecionadas, id])
  }

  return (
    <div className="flex flex-col gap-2">
      {competencias.length > LIMITE_SEM_FILTRO && (
        <div className="relative w-full sm:max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
          <input
            type="text"
            value={filtro}
            onChange={(e) => setFiltro(e.target.value)}
            placeholder="Filtrar competências"
            aria-label={`Filtrar ${rotulo.toLowerCase()}`}
            className="w-full h-9 bg-(--surface-elevated) outline-none rounded-lg pl-9 pr-3 text-sm text-white border border-gray-700/50 focus:ring-2 focus:ring-primary transition duration-200"
          />
        </div>
      )}

      <div role="group" aria-label={rotulo} aria-describedby={descritoPor} className="flex flex-wrap gap-2">
        {visiveis.map((c) => {
          const marcada = selecionadas.includes(c.id)
          return (
            <button
              key={c.id}
              type="button"
              onClick={() => alternar(c.id)}
              aria-pressed={marcada}
              disabled={desabilitado}
              className={`h-8 px-3 rounded-full text-sm border transition-colors disabled:opacity-50 ${
                marcada
                  ? "bg-primary text-white border-primary"
                  : "bg-(--surface-elevated) text-secondary border-gray-700/50 hover:text-white"
              }`}
            >
              {c.nome}
            </button>
          )
        })}
        {visiveis.length === 0 && (
          <span className="text-sm text-secondary">Nenhuma competência encontrada.</span>
        )}
      </div>

      {selecionadas.length > 0 && (
        <span className="text-xs text-secondary">
          {selecionadas.length} {selecionadas.length === 1 ? "selecionada" : "selecionadas"}
        </span>
      )}
    </div>
  )
}