"use client"
import { useEffect, useState } from "react"
import {
  ClipboardCheck,
  FileText,
  FolderOpen,
  MessageSquare,
} from "lucide-react"

type Resumo = {
  projetos: number
  documentos: {
    total: number
    processados: number
    processando: number
    com_erro: number
    percentual_indexado: number
  }
  conversas: number
  validacoes: number
}

export default function DashboardCards() {
  const [resumo, setResumo] = useState<Resumo | null>(null)

  useEffect(() => {
    fetch("http://localhost:8000/api/dashboard/resumo/", {
      credentials: "include",
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(setResumo)
      .catch(() => setResumo(null))
  }, [])

  const cards = [
    {
      rotulo: "Projetos",
      valor: resumo?.projetos,
      icone: FolderOpen,
    },
    {
      rotulo: "Documentos",
      valor: resumo?.documentos.total,
      icone: FileText,
      detalhe: resumo
        ? `${resumo.documentos.percentual_indexado}% indexados`
        : undefined,
      alerta:
        resumo && resumo.documentos.com_erro > 0
          ? `${resumo.documentos.com_erro} com erro`
          : undefined,
    },
    {
      rotulo: "Conversas",
      valor: resumo?.conversas,
      icone: MessageSquare,
    },
    {
      rotulo: "Validações",
      valor: resumo?.validacoes,
      icone: ClipboardCheck,
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(({ rotulo, valor, icone: Icone, detalhe, alerta }) => (
        <div
          key={rotulo}
          className="rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4 flex flex-col gap-1"
        >
          <div className="flex items-center justify-between text-(--primary)">
            <span className="text-xs font-semibold uppercase tracking-wider">
              {rotulo}
            </span>
            <Icone size={18} />
          </div>
          <span className="text-3xl font-bold text-white">{valor ?? "—"}</span>
          {detalhe && (
            <span className="text-xs text-(--foreground-muted)">{detalhe}</span>
          )}
          {alerta && (
            <span className="text-xs font-medium text-red-400">{alerta}</span>
          )}
        </div>
      ))}
    </div>
  )
}
