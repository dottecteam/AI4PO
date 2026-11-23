"use client"

import { useState } from "react"
import Link from "next/link"
import { CircleCheck, CircleX, ClipboardList } from "lucide-react"
import { api } from "@/app/services/API/api"

export type AcaoChat = {
  id: string
  mensagem_id: number
  tipo: "projeto" | "profissional" | "competencia" | "usuario"
  estado: "pendente" | "confirmada" | "cancelada"
  dados: Record<string, string | string[]>
  resultado?: { id: number; link: string }
}

type RespostaDecisao = { message: string; acao: AcaoChat; senha_temporaria?: string }

const TITULOS: Record<AcaoChat["tipo"], string> = {
  projeto: "Novo projeto",
  profissional: "Novo profissional",
  competencia: "Nova competência",
  usuario: "Novo login de PO",
}

const CAMPOS: Record<string, string> = {
  titulo: "Título",
  descricao: "Descrição",
  status: "Status",
  nome: "Nome",
  email: "E-mail",
  competencias: "Competências",
  competencias_novas: "Competências novas (serão criadas)",
}

// O helper `api` lança Error com o corpo JSON; extrai a mensagem do campo "error"
function mensagemDoErro(erro: unknown) {
  try {
    return JSON.parse((erro as Error).message).error ?? "Não foi possível concluir o cadastro."
  } catch {
    return "Não foi possível concluir o cadastro."
  }
}

type Props = {
  acao: AcaoChat
  onAtualizada: (acao: AcaoChat) => void
}

export default function CartaoAcao({ acao, onAtualizada }: Props) {
  const [enviando, setEnviando] = useState(false)
  const [erro, setErro] = useState("")
  // A senha temporária só existe nesta resposta: não volta no histórico
  const [senha, setSenha] = useState("")

  const decidir = async (decisao: "confirmar" | "cancelar") => {
    setEnviando(true)
    setErro("")
    try {
      const r = await api.post<RespostaDecisao>(`/api/chat/acoes/${acao.mensagem_id}/${decisao}/`, {})
      if (r.senha_temporaria) setSenha(r.senha_temporaria)
      onAtualizada(r.acao)
    } catch (e) {
      setErro(mensagemDoErro(e))
    } finally {
      setEnviando(false)
    }
  }

  const linhas = Object.entries(acao.dados).filter(([, valor]) =>
    Array.isArray(valor) ? valor.length > 0 : !!valor,
  )

  return (
    <div className="mt-2 rounded-xl border border-gray-700/60 bg-black/20 p-3 flex flex-col gap-3">
      <div className="flex items-center gap-2 text-white text-sm font-semibold">
        <ClipboardList size={16} className="text-primary" />
        {TITULOS[acao.tipo]}
      </div>

      <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1.5 text-xs">
        {linhas.map(([campo, valor]) => (
          <div key={campo} className="contents">
            <dt className="text-secondary">{CAMPOS[campo] ?? campo}</dt>
            <dd className="text-gray-200 break-words">{Array.isArray(valor) ? valor.join(", ") : valor}</dd>
          </div>
        ))}
      </dl>

      {acao.estado === "pendente" ? (
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => decidir("confirmar")}
            disabled={enviando}
            className="h-8 px-3 rounded-lg text-xs font-medium text-white bg-primary hover:bg-primary-dark transition-colors disabled:opacity-50 cursor-pointer"
          >
            {enviando ? "Salvando..." : "Confirmar cadastro"}
          </button>
          <button
            type="button"
            onClick={() => decidir("cancelar")}
            disabled={enviando}
            className="h-8 px-3 rounded-lg text-xs text-white border border-gray-700/60 hover:bg-(--surface-base) transition-colors disabled:opacity-50 cursor-pointer"
          >
            Cancelar
          </button>
        </div>
      ) : acao.estado === "confirmada" ? (
        <div className="flex flex-col gap-1.5 text-xs">
          <span className="flex items-center gap-1.5 text-green-400">
            <CircleCheck size={14} /> Cadastro salvo.
            {acao.resultado?.link && (
              <Link href={acao.resultado.link} className="text-primary hover:underline ml-1">
                Abrir
              </Link>
            )}
          </span>
          {senha && (
            <span className="text-gray-200">
              Senha temporária (mostrada só agora; repasse ao PO e peça para trocar):{" "}
              <code className="text-primary-light select-all">{senha}</code>
            </span>
          )}
        </div>
      ) : (
        <span className="flex items-center gap-1.5 text-xs text-secondary">
          <CircleX size={14} /> Cadastro cancelado.
        </span>
      )}

      {erro && (
        <p role="alert" className="text-xs text-red-300">
          {erro}
        </p>
      )}
    </div>
  )
}
