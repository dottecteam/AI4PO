"use client"

import { useEffect, useRef, useState } from "react"
import { Send, Paperclip, ChevronDown, Funnel, FileText, X } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

const extensoes = [".txt", ".md"]
const tamanho_max = 10 * 1024 * 1024

type Mensagem = {
  tipo: "usuario" | "agente" | "anexo"
  texto: string
  anexo?: string
}

type MensagemApi = {
  papel: "user" | "assistant"
  conteudo: string
  anexo_nome: string
}

function getCookie(name: string) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(name + "="))
    ?.split("=")[1];
}

function ChatBot({ conversaIdInicial }: { conversaIdInicial?: number }) {
  const [mensagem, setMensagem] = useState("")
  const [mensagens, setMensagens] = useState<Mensagem[]>([])
  const [carregando, setCarregando] = useState(false)
  const [anexos, setAnexos] = useState<File[]>([])
  const [conversaId, setConversaId] = useState<number | null>(conversaIdInicial ?? null)
  const inputArquivoRef = useRef<HTMLInputElement>(null)
  const fimMensagensRef = useRef<HTMLDivElement>(null)

  // Ao abrir uma conversa existente (vinda da sidebar), carrega o histórico salvo
  useEffect(() => {
    if (!conversaIdInicial) return

    fetch(`http://localhost:8000/api/conversas/${conversaIdInicial}/mensagens/`, {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data: { mensagens: MensagemApi[] }) => {
        const carregadas: Mensagem[] = data.mensagens.map((m) => ({
          tipo: m.papel === "user" ? "usuario" : "agente",
          texto: m.conteudo,
          anexo: m.anexo_nome || undefined,
        }))
        setMensagens(carregadas)
      })
      .catch(() => setMensagens([]))
  }, [conversaIdInicial])

  useEffect(() => {
    fimMensagensRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [mensagens, carregando])

  const abrirSeletorDeArquivo = () => {
    inputArquivoRef.current?.click()
  }

  //só guarda o arquivo em memória, nenhum upload acontece aq nem se enviar
  const arquivoSelecionado = (event: React.ChangeEvent<HTMLInputElement>) => {
    const arquivo = event.target.files?.[0]
    event.target.value = ""
    if (!arquivo) return

    const extensao = "." + arquivo.name.split(".").pop()?.toLowerCase()
    if (!extensoes.includes(extensao)) {
      alert(`Tipo de arquivo não suportado. Envie ${extensoes.join(" ou ")}.`)
      return
    }
    if (arquivo.size > tamanho_max) {
      alert("Arquivo maior que 10 MB.")
      return
    }

    setAnexos((prev) => [...prev, arquivo])
  }

  const removerAnexo = (index: number) => {
    setAnexos((prev) => prev.filter((_, i) => i !== index))
  }

  const enviarMensagem = async () => {
    if ((!mensagem.trim() && anexos.length === 0) || carregando) return

    if (anexos.length > 1) {
      alert("Por enquanto só é possível enviar um documento por mensagem.")
      return
    }

    const arquivoParaEnvio = anexos[0]
    const mensagemUsuario = mensagem
    setAnexos([])

    // anexo sozinho, sem texto: só mostra o card, não chama o backend
    // (nenhuma mensagem salva no histórico nesse caso)
    if (!mensagemUsuario.trim()) {
      if (arquivoParaEnvio) {
        setMensagens((prev) => [
          ...prev,
          { tipo: "usuario", texto: "", anexo: arquivoParaEnvio.name },
        ])
      }
      return
    }

    setMensagens((prev) => [
      ...prev,
      {
        tipo: "usuario",
        texto: mensagemUsuario,
        anexo: arquivoParaEnvio?.name,
      },
    ])

    setMensagem("")
    setCarregando(true)

     try {
      let response
      const csrfToken = getCookie("csrftoken") ?? ""

      if (arquivoParaEnvio) {
        const formData = new FormData()
        formData.append("message", mensagemUsuario)
        formData.append("arquivo", arquivoParaEnvio)
        if (conversaId) formData.append("conversa_id", String(conversaId))

        response = await fetch("http://localhost:8000/api/chat/", {
          method: "POST",
          credentials: "include",
          headers: { "X-CSRFToken": csrfToken }, // sem Content-Type: o navegador define o boundary
          body: formData,
        })
      } else {
        response = await fetch("http://localhost:8000/api/chat/", {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            message: mensagemUsuario,
            conversa_id: conversaId,
          }),
        })
      }

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || data.details || data.error || "Erro ao conversar com o agente.")
      }

      setConversaId(data.conversa_id)
      setMensagens((prev) => [...prev, { tipo: "agente", texto: data.message }])
    } catch (error) {
      console.error("Erro:", error)
      setMensagens((prev) => [
        ...prev,
        { tipo: "agente", texto: "Não foi possível conectar ao agente." },
      ])
    } finally {
      setCarregando(false)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") enviarMensagem()
  }

  return (
    <div className="w-full h-full flex flex-col flex-1 bg-background">

      {/* Header do Chat */}
      <div className="w-full shrink-0 flex justify-between items-center px-4 sm:px-6 lg:px-8 py-4 bg-background border-b border-gray-800/50 z-10">
        <div className="w-auto flex flex-col gap-1 min-w-0">
          <h1 className="text-white font-semibold text-lg sm:text-2xl lg:text-3xl truncate">
            Assistente RAG Pro4Tech
          </h1>
          <span className="flex items-center gap-2 text-secondary text-xs sm:text-sm">
            <div className="bg-green-500 w-2.5 h-2.5 rounded-full shrink-0 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
            <span className="hidden sm:inline">Contexto ativo: Base de Conhecimentos</span>
          </span>
        </div>

        <div className="w-auto h-10 bg-(--surface-elevated) rounded-lg flex justify-center items-center px-3 shrink-0 cursor-pointer hover:bg-(--surface-base) transition-colors border border-gray-800/50">
          <button type="button" className="flex items-center justify-center p-1 pr-2 border-r border-gray-700">
            <ChevronDown size={20} className="text-white" />
          </button>
          <div className="flex flex-row gap-2 items-center pl-2">
            <Funnel size={18} className="text-white shrink-0" />
            <span className="text-white font-medium select-none text-sm hidden md:block whitespace-nowrap">
              Filtros de Busca
            </span>
          </div>
        </div>
      </div>

      {/* Área de Mensagens */}
      <div className="w-full flex-1 min-h-0 overflow-y-auto flex flex-col gap-4 px-4 sm:px-6 lg:px-8 py-6 bg-background">
        {mensagens.map((msg, index) => (
          <div key={index} className={`flex ${msg.tipo === "usuario" ? "justify-end" : "justify-start"}`}>
            <div
              className={`relative max-w-[85%] rounded-2xl px-5 py-3 text-sm sm:text-base shadow-sm ${
                msg.tipo === "usuario"
                  ? "bg-primary text-white rounded-tr-sm"
                  : "bg-(--surface-elevated) text-gray-200 rounded-tl-sm border border-gray-800/50"
              }`}
            >
              {msg.anexo && (
                <div className="flex items-center gap-2 rounded-md bg-black/20 px-3 py-2 mb-2">
                  <FileText size={16} className="shrink-0 text-white" />
                  <span className="truncate text-xs font-medium">{msg.anexo}</span>
                </div>
              )}
              {msg.texto && (msg.tipo === "agente" ? (
                <div className="markdown-mensagem prose prose-invert prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-pre:bg-(--surface-base) prose-code:text-primary-light">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.texto}</ReactMarkdown>
                </div>
              ) : (
                msg.texto
              ))}
            </div>
          </div>
        ))}
        {carregando && (
          <div className="flex justify-start">
            <div className="bg-(--surface-elevated) text-secondary rounded-2xl rounded-tl-sm px-5 py-3 text-sm animate-pulse border border-gray-800/50">
              Analisando documentos...
            </div>
          </div>
        )}
        <div ref={fimMensagensRef} />
      </div>

      {/* Input de Mensagem */}
      <div className="w-full shrink-0 bg-(--surface-base) rounded-t-3xl border-t border-gray-800/50 shadow-[0_-4px_25px_rgba(0,0,0,0.15)] flex flex-col justify-center gap-2 px-2 sm:px-4 lg:px-6 py-3 relative z-20">
        {anexos.length > 0 && (
          <div className="flex gap-2 flex-wrap mb-2">
            {anexos.map((arquivo, index) => (
              <div key={index} className="relative w-36 h-20 bg-(--surface-elevated) rounded-lg p-3 flex flex-col justify-between border border-primary transition duration-200">
                <button type="button" onClick={() => removerAnexo(index)} className="absolute top-1 right-1 text-white/60 hover:text-white p-1">
                  <X size={16} />
                </button>
                <span className="text-xs text-secondary font-bold select-none">{arquivo.name.split(".").pop()?.toUpperCase()}</span>
                <span className="text-xs text-white truncate select-none">{arquivo.name}</span>
              </div>
            ))}
          </div>
        )}

        <div className="w-full max-w-4xl mx-auto flex items-center gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={mensagem}
              onChange={(event) => setMensagem(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Pergunte sobre regras, decisões arquiteturais..."
              className="w-full h-12 md:h-14 bg-(--surface-elevated) outline-none rounded-xl pl-4 pr-12 text-sm sm:text-base text-white focus:ring-2 focus:ring-primary border border-gray-700/50 transition duration-200"
            />
            <input ref={inputArquivoRef} type="file" accept={extensoes.join(",")} onChange={arquivoSelecionado} className="hidden" />
            <button type="button" onClick={abrirSeletorDeArquivo} className="absolute right-2 top-1/2 -translate-y-1/2 p-2 hover:bg-gray-700/50 rounded-lg transition-colors">
              <Paperclip size={20} className="text-secondary hover:text-white" />
            </button>
          </div>
          <button
            type="button"
            onClick={enviarMensagem}
            disabled={carregando || (!mensagem.trim() && anexos.length === 0)}
            className="w-12 h-12 md:w-14 md:h-14 bg-primary rounded-xl flex items-center justify-center hover:bg-primary-dark transition-colors duration-200 shrink-0 disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
          >
            <Send size={20} className="text-white" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatBot