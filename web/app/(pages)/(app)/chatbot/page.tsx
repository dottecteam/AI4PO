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
}

function ChatBot() {
  const [mensagem, setMensagem] = useState("")
  const [mensagens, setMensagens] = useState<Mensagem[]>([])
  const [carregando, setCarregando] = useState(false)
  const [anexos, setAnexos] = useState<File[]>([])
  const inputArquivoRef = useRef<HTMLInputElement>(null)
  const fimMensagensRef = useRef<HTMLDivElement>(null)
  //rola automaticamente para o fim sempre que mensagens ou o estado de carregando mudam
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

    // por enquanto, só mostra o anexo na conversa, até a gente definir o que vamos fazer
    for (const arquivo of anexos) {
      setMensagens((prev) => [...prev, { tipo: "anexo", texto: arquivo.name }])
    }
    setAnexos([])

    if (!mensagem.trim()) return

    const mensagemUsuario = mensagem

    setMensagens((prev) => [
      ...prev,
      { tipo: "usuario", texto: mensagemUsuario },
    ])

    setMensagem("")
    setCarregando(true)

    try {
      const response = await fetch("http://localhost:8000/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: mensagemUsuario }),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.error || "Erro ao conversar com o agente.")
      }
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
    <div className="w-full h-full bg-[#010812] grid grid-rows-[10%_1fr_auto]">
      <div className="w-full h-full bg-[#010812] flex justify-between items-center px-4 sm:px-6 lg:px-8">
        <div className="w-auto h-auto flex flex-col gap-1 min-w-0">
          <h1 className="text-white font-semibold text-lg sm:text-2xl lg:text-3xl truncate">
            Assistente RAG Pro4Tech
          </h1>
          <span className="flex items-center gap-1 text-[#AEC5F4] text-xs sm:text-sm">
            <div className="bg-green-500 w-2 h-2 rounded-[999px] shrink-0" />
            <span className="hidden sm:inline">Contexto ativo:</span>
          </span>
        </div>

        <div className="w-auto sm:w-1/3 lg:w-[12.5%] h-1/2 bg-[#212838] rounded-lg flex justify-center items-center gap-2 px-3 shrink-0">
          <button
            type="button"
            className="flex items-center justify-center rounded-lg hover:bg-[#333D55] transition duration-200 p-1"
          >
            <ChevronDown size={20} color={"white"} />
          </button>
          <div className="flex flex-row gap-2 items-center">
            <Funnel size={20} color="white" className="shrink-0" />
            <h1 className="text-white select-none text-sm hidden md:block whitespace-nowrap">
              Filtros de Busca
            </h1>
          </div>
        </div>
      </div>

      {/* chatbot */}
      <div className="w-full h-full min-h-0 overflow-y-auto flex flex-col gap-3 px-4 sm:px-6 lg:px-8 py-4 bg-linear-to-b from-[#010812] to-[#0C1322]">
        {mensagens.map((msg, index) => {
          if (msg.tipo === "anexo") {
            return (
              <div key={index} className="flex justify-end">
                <div className="flex items-center gap-2 max-w-[80%] rounded-lg px-4 py-3 text-sm sm:text-base bg-[#333D55] text-white">
                  <FileText size={18} className="shrink-0 text-[#EF7541]" />
                  <span className="truncate">{msg.texto}</span>
                </div>
              </div>
            )
          }
          return (
            <div
              key={index}
              className={`flex ${msg.tipo === "usuario" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`relative max-w-[80%] rounded-lg px-4 py-3 text-sm sm:text-base ${
                  msg.tipo === "usuario"
                    ? "bg-[#EF7541] text-white rounded-tr-none"
                    : "bg-[#212838] text-[#AEC5F4] rounded-tl-none"
                }`}
              >
                {/* pontinha do usuario*/}
                {msg.tipo === "usuario" && (
                  <span
                    className="absolute bottom-full right-0 w-3 h-3 bg-[#EF7541]"
                    style={{ clipPath: "polygon(100% 100%, 100% 0, 0 100%)" }}
                  />
                )}

                {/* pontinha do agente */}
                {msg.tipo === "agente" && (
                  <span
                    className="absolute bottom-full left-0 w-3 h-3 bg-[#212838]"
                    style={{ clipPath: "polygon(0 100%, 0 0, 100% 100%)" }}
                  />
                )}

                {msg.tipo === "agente" ? (
                  <div className="markdown-mensagem prose prose-invert prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-pre:bg-[#0C1322] prose-code:text-[#EF7541]">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.texto}
                    </ReactMarkdown>
                  </div>
                ) : (
                  msg.texto
                )}
              </div>
            </div>
          )
        })}

        {carregando && (
          <div className="flex justify-start">
            <div className="relative bg-[#212838] text-[#AEC5F4] rounded-lg rounded-tl-none px-4 py-3 text-sm sm:text-base">
              <span className="absolute -top-2 left-0 w-3 h-3 bg-[#212838]" />
              Pensando...
            </div>
          </div>
        )}
        <div ref={fimMensagensRef} />
      </div>

      <div className="w-full bg-[#010812] flex flex-col justify-center gap-2 px-4 sm:px-6 lg:px-8 py-3">
        {anexos.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            {anexos.map((arquivo, index) => (
              <div
                key={index}
                className="relative w-36 h-20 bg-[#212838] rounded-lg p-3 flex flex-col justify-between border border-[#EF7541] hover:border-[#AEC5F4] transition duration-200 "
              >
                <button
                  type="button"
                  onClick={() => removerAnexo(index)}
                  className="absolute top-1 right-1 text-white/60 hover:text-white p-0.5"
                >
                  <X size={14} />
                </button>
                <span className="text-xs text-[#AEC5F4] font-medium select-none">
                  {arquivo.name.split(".").pop()?.toUpperCase()}
                </span>
                <span className="text-xs text-white truncate select-none">
                  {arquivo.name}
                </span>
              </div>
            ))}
          </div>
        )}

        <div className="w-full h-12 sm:h-14 flex justify-center items-center gap-3 sm:gap-6">
          <div className="relative flex-1 h-full">
            <input
              type="text"
              value={mensagem}
              onChange={(event) => setMensagem(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Pergunte sobre regras, decisões arquiteturais ou histórico de projetos..."
              className="w-full h-full bg-[#212838] outline-none rounded-lg pl-3 sm:pl-4 pr-10 sm:pr-12 text-sm sm:text-base text-white focus:ring-2 focus:ring-[#EF7541] transition duration-200"
            />
            <input
              ref={inputArquivoRef}
              type="file"
              accept={extensoes.join(",")}
              onChange={arquivoSelecionado}
              className="hidden"
            />
            <button
              type="button"
              onClick={abrirSeletorDeArquivo}
              className="absolute right-2 sm:right-3 top-1/2 -translate-y-1/2 flex items-center justify-center cursor-pointer"
            >
              <Paperclip
                size={20}
                className="sm:w-6 sm:h-6"
                color={"#AEC5F4"}
              />
            </button>
          </div>

          <button
            type="button"
            onClick={enviarMensagem}
            disabled={carregando || (!mensagem.trim() && anexos.length === 0)}
            className="w-12 h-12 sm:w-16 sm:h-14 bg-[#EF7541] rounded-lg flex items-center justify-center cursor-pointer hover:bg-[#d9653a] transition-colors duration-200 shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={22} className="sm:w-7 sm:h-7" color={"white"} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatBot
