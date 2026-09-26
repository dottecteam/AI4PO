"use client"

import { Documento, EstadoDocumento } from "@/app/types/api/documento"
import { api } from "@/app/services/API/api"
import { useEffect, useRef, useState } from "react"

interface DocumentoCardProps {
  documento: Documento
  onReprocessado?: () => void
}

const ESTADO_STYLES: Record<
  EstadoDocumento,
  { label: string; className: string }
> = {
  pendente: { label: "Pendente", className: "bg-gray-600" },
  processando: { label: "Processando", className: "bg-blue-600 animate-pulse" },
  processado: { label: "Processado", className: "bg-green-600" },
  erro: { label: "Erro", className: "bg-red-600" },
}

function EstadoBadge({ estado }: { estado: EstadoDocumento }) {
  const { label, className } = ESTADO_STYLES[estado]
  return (
    <span className={`rounded px-2 py-1 text-xs font-bold ${className}`}>
      {label}
    </span>
  )
}

export default function DocumentoCard({
  documento,
  onReprocessado,
}: DocumentoCardProps) {
  const dataFormatada = new Date(documento.data).toLocaleDateString("pt-BR")

  const [menuAberto, setMenuAberto] = useState(false)
  const [reprocessando, setReprocessando] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuAberto(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)

    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [])

  function excluirDocumento() {
    console.log("Excluir documento", documento.nome)
  }

  async function reprocessarDocumento() {
    setReprocessando(true)
    try {
      await api.post(
        `/api/projects/${documento.projetoId}/documents/${documento.id}/reprocess/`,
        {},
      )
      onReprocessado?.()
    } catch (erro) {
      console.error("Falha ao reprocessar documento", erro)
    } finally {
      setReprocessando(false)
    }
  }

  return (
    <div
      className="w-full rounded-xl bg-[#212838] p-5 border border-transparent"
      key={documento.id}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex gap-2">
          <span className={`rounded px-2 py-1 text-xs font-bold bg-[#EF7541]`}>
            {documento.tipo}
          </span>
          <EstadoBadge estado={documento.estado} />
        </div>

        {/* menu */}
        <div className="relative ml-4" ref={menuRef}>
          <button
            onClick={() => setMenuAberto(!menuAberto)}
            className="flex size-9 items-center justify-center rounded-full text-gray-400 hover:bg-gray-800 hover:text-white"
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
              <circle cx="5" cy="12" r="1.5" />
              <circle cx="12" cy="12" r="1.5" />
              <circle cx="19" cy="12" r="1.5" />
            </svg>
          </button>

          {menuAberto && (
            <div className="absolute right-0 top-11 z-20 w-48 overflow-hidden rounded-lg border border-gray-700 bg-[#111827] shadow-xl">
              {documento.estado === "erro" && (
                <button
                  onClick={reprocessarDocumento}
                  disabled={reprocessando}
                  className="w-full px-4 py-3 text-left text-sm text-white hover:bg-gray-800 disabled:opacity-50"
                >
                  {reprocessando ? "Reprocessando..." : "Reprocessar"}
                </button>
              )}
              <div className="border-t border-gray-700" />
              <button
                onClick={excluirDocumento}
                className="w-full px-4 py-3 text-left text-sm text-red-400 hover:bg-gray-800"
              >
                Excluir
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Nome */}
      <p className="w-full py-1 text-lg text-white border-b-1 border-[#F7C09A]">
        {documento.nome}
      </p>

      {/* data */}
      <p className="text-sm text-white px-3 pt-2">{dataFormatada}</p>

      {/* mensagem de erro */}
      {documento.estado === "erro" && documento.mensagemErro && (
        <p className="text-xs text-red-400 px-3 pt-2">
          {documento.mensagemErro}
        </p>
      )}
    </div>
  )
}
