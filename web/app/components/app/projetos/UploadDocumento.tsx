"use client"

import { useState } from "react"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL

// O Django exige o token CSRF (cookie) no POST; no XHR precisamos enviá-lo à mão.
function getCookie(name: string): string | undefined {
  if (typeof document === "undefined") return undefined
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(name + "="))
    ?.split("=")[1]
}

// Estima o tempo que falta no upload, pela taxa de bytes enviados.
function formatarTempoRestante(segundos: number): string {
  if (!isFinite(segundos) || segundos <= 0) return "calculando..."
  if (segundos < 60) return `~${Math.round(segundos)}s restantes`
  const m = Math.floor(segundos / 60)
  const s = Math.round(segundos % 60)
  return `~${m}min${s ? ` ${s}s` : ""} restantes`
}

// Formata uma duração total ("213s" -> "3min 33s").
function formatarDuracao(segundos: number | null): string {
  if (segundos == null) return "poucos segundos"
  if (segundos < 60) return `${Math.round(segundos)}s`
  const m = Math.floor(segundos / 60)
  const s = Math.round(segundos % 60)
  return `${m}min${s ? ` ${s}s` : ""}`
}

interface DocumentoUploadProps {
  aberto: boolean
  onFechar: () => void
  projetoId: number
  onEnviado: () => void
}

// Fases visíveis na barra: envio do arquivo -> geração do grafo -> pronto.
type Fase = "idle" | "enviando" | "grafo" | "pronto"

export default function UploadDocumento({
  aberto,
  onFechar,
  projetoId,
  onEnviado,
}: DocumentoUploadProps) {
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [erro, setErro] = useState("")
  const [fase, setFase] = useState<Fase>("idle")
  const [progresso, setProgresso] = useState(0)
  const [tempoRestante, setTempoRestante] = useState("")
  const [grafoPct, setGrafoPct] = useState(0)
  const [mensagemFinal, setMensagemFinal] = useState("")

  const ocupado = fase === "enviando" || fase === "grafo"

  function reiniciar() {
    setArquivo(null)
    setErro("")
    setFase("idle")
    setProgresso(0)
    setTempoRestante("")
    setGrafoPct(0)
    setMensagemFinal("")
  }

  function fechar() {
    reiniciar()
    onFechar()
  }

  // Consulta o backend em polling até o GraphRAG terminar, alimentando a barra de %.
  async function acompanharGrafo(documentoId: number) {
    setFase("grafo")
    setGrafoPct(0)
    while (true) {
      try {
        const resp = await fetch(`${BASE_URL}/api/grafo/status/${documentoId}/`, {
          credentials: "include",
        })
        if (resp.ok) {
          const d = await resp.json()
          if (d.status === "concluido") {
            setGrafoPct(100)
            setMensagemFinal(`Grafo criado em ${formatarDuracao(d.segundos_totais)}.`)
            setFase("pronto")
            setTimeout(() => {
              onEnviado()
              fechar()
            }, 1600)
            return
          }
          if (d.status === "erro") {
            setErro("O documento foi enviado, mas a geração do grafo falhou.")
            setFase("pronto")
            setTimeout(() => {
              onEnviado()
              fechar()
            }, 2600)
            return
          }
          setGrafoPct(d.percentual ?? 0)
        }
      } catch {
        // falha transitória de rede no polling: tenta de novo
      }
      await new Promise((r) => setTimeout(r, 2000))
    }
  }

  function enviarDocumento() {
    if (!arquivo) {
      setErro("Selecione um arquivo antes de enviar.")
      return
    }

    setErro("")
    setFase("enviando")
    setProgresso(0)
    setTempoRestante("calculando...")
    setGrafoPct(0)
    setMensagemFinal("")

    const formData = new FormData()
    formData.append("arquivo", arquivo)

    // fetch() não expõe progresso de upload; usamos XMLHttpRequest para a barrinha de %.
    const xhr = new XMLHttpRequest()
    xhr.open("POST", `${BASE_URL}/api/projects/${projetoId}/documents/upload/`)
    xhr.withCredentials = true
    const csrf = getCookie("csrftoken")
    if (csrf) xhr.setRequestHeader("X-CSRFToken", csrf)

    const inicio = Date.now()
    xhr.upload.onprogress = (evento) => {
      if (!evento.lengthComputable) return
      const pct = Math.round((evento.loaded / evento.total) * 100)
      setProgresso(pct)
      const decorrido = (Date.now() - inicio) / 1000
      if (pct > 0 && decorrido > 0) {
        const totalEstimado = decorrido / (pct / 100)
        setTempoRestante(formatarTempoRestante(Math.max(0, totalEstimado - decorrido)))
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        setProgresso(100)
        let docId: number | null = null
        try {
          docId = JSON.parse(xhr.responseText)?.id ?? null
        } catch {
          docId = null
        }
        if (docId != null) {
          acompanharGrafo(docId)
        } else {
          onEnviado()
          fechar()
        }
      } else {
        setFase("idle")
        setErro(
          "Não foi possível enviar o documento. Verifique o formato/tamanho e tente de novo.",
        )
        console.error("Erro ao enviar documento:", xhr.status, xhr.responseText)
      }
    }

    xhr.onerror = () => {
      setFase("idle")
      setErro("Falha de rede ao enviar o documento. Tente novamente.")
    }

    xhr.send(formData)
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
              disabled={ocupado}
              onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
              className="mt-1 w-full rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm text-gray-200 outline-none file:mr-3 file:rounded file:border-0 file:bg-[#EF7541] file:px-3 file:py-1.5 file:text-white disabled:opacity-50"
            />

            {arquivo && (
              <p className="mt-2 text-xs text-gray-400">
                Selecionado: {arquivo.name}
              </p>
            )}
          </div>

          {/* Barra de progresso: envio do arquivo */}
          {fase === "enviando" && (
            <div>
              <div className="mb-1 flex items-center justify-between text-xs text-gray-400">
                <span>Enviando {arquivo?.name}</span>
                <span>{progresso}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-gray-800">
                <div
                  className="h-full rounded-full bg-[#EF7541] transition-all duration-200"
                  style={{ width: `${progresso}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">{tempoRestante}</p>
            </div>
          )}

          {/* Barra de progresso: geração do GraphRAG */}
          {fase === "grafo" && (
            <div>
              <div className="mb-1 flex items-center justify-between text-xs text-gray-400">
                <span>Gerando grafo de conhecimento (GraphRAG)…</span>
                <span>{grafoPct}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-gray-800">
                <div
                  className="h-full rounded-full bg-[#EF7541] transition-all duration-500"
                  style={{ width: `${grafoPct}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Pode levar alguns minutos. Você já pode perguntar sobre o documento.
              </p>
            </div>
          )}

          {/* Conclusão */}
          {fase === "pronto" && mensagemFinal && (
            <p className="text-sm text-green-400">{mensagemFinal}</p>
          )}
        </div>

        {erro && <p className="text-sm text-red-500 text-left px-6">{erro}</p>}

        {/* Footer */}
        <div className="sticky bottom-0 flex justify-end gap-3 border-t border-gray-800 bg-[#080d16] px-6 py-4">
          <button
            onClick={fechar}
            disabled={fase === "grafo"}
            className="rounded-md px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 disabled:opacity-40"
          >
            Cancelar
          </button>

          <button
            onClick={enviarDocumento}
            disabled={ocupado}
            className="rounded-md bg-[#EF7541] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            {fase === "enviando"
              ? "Enviando..."
              : fase === "grafo"
                ? "Gerando grafo..."
                : "Enviar"}
          </button>
        </div>
      </div>
    </div>
  )
}
