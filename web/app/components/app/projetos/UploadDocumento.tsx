"use client"

import { api } from "@/app/services/API/api"
import { useState } from "react"

interface DocumentoUploadProps {
  aberto: boolean
  onFechar: () => void
  projetoId: number
  onEnviado: () => void
}

export default function UploadDocumento({
  aberto,
  onFechar,
  projetoId,
  onEnviado,
}: DocumentoUploadProps) {
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState("")

  function fechar() {
    setArquivo(null)
    setErro("")
    onFechar()
  }

  async function enviarDocumento() {
    if (!arquivo) {
      setErro("Selecione um arquivo antes de enviar.")
      return
    }

    setEnviando(true)
    setErro("")

    try {
      const formData = new FormData()
      formData.append("arquivo", arquivo)

      await api.postForm(
        `/api/projects/${projetoId}/documents/upload/`,
        formData,
      )

      setArquivo(null)
      onEnviado()
      onFechar()
    } catch (e) {
      setErro(
        "Não foi possível enviar o documento. Verifique o formato/tamanho e tente de novo.",
      )
      console.error("Erro ao enviar documento:", e)
    } finally {
      setEnviando(false)
    }
  }

  if (!aberto) return null

  return (
    <div className="fixed inset-0 z-50 max-h-screen flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-xl border border-gray-900 bg-[#080d16] shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-800 bg-[#080d16] px-6 py-5">
          <h2 className="font-semibold tracking-wider text-[#EF7541]">
            Enviar Documento
          </h2>

          <button
            onClick={fechar}
            className="flex size-9 items-center justify-center rounded-full text-gray-400 hover:bg-gray-800 hover:text-white"
          >
            <svg
              viewBox="0 0 24 24"
              className="h-6 w-6 rotate-45 text-[#EF7541]"
              fill="none"
            >
              <path
                d="M11.83 7.5v8.67M7.5 11.83h8.67M22.67 11.83a10.83 10.83 0 1 1-21.67 0 10.83 10.83 0 0 1 21.67 0Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>

        {/* Formulário */}
        <div className="space-y-6 px-6 py-6">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
              Arquivo (.txt ou .md)
            </label>

            <input
              type="file"
              accept=".txt,.md"
              onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
              className="mt-1 w-full rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm text-gray-200 outline-none file:mr-3 file:rounded file:border-0 file:bg-[#EF7541] file:px-3 file:py-1.5 file:text-white"
            />

            {arquivo && (
              <p className="mt-2 text-xs text-gray-400">
                Selecionado: {arquivo.name}
              </p>
            )}
          </div>
        </div>

        {erro && <p className="text-sm text-red-500 text-left px-6">{erro}</p>}

        {/* Footer */}
        <div className="sticky bottom-0 flex justify-end gap-3 border-t border-gray-800 bg-[#080d16] px-6 py-4">
          <button
            onClick={fechar}
            className="rounded-md px-4 py-2 text-sm text-gray-300 hover:bg-gray-800"
          >
            Cancelar
          </button>

          <button
            onClick={enviarDocumento}
            disabled={enviando}
            className="rounded-md bg-[#EF7541] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            {enviando ? "Enviando..." : "Enviar"}
          </button>
        </div>
      </div>
    </div>
  )
}
