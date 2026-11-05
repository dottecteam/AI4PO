"use client"
import { useEffect, useState } from "react"
import {
  Activity,
  BookOpen,
  FileText,
  LucideIcon,
  MessageSquare,
  Pencil,
  Trash2,
} from "lucide-react"

type Atividade = {
  id: number
  acao: string
  usuario: string
  texto: string
  alvo: string
  detalhe?: string
  criado_em: string
}

const ICONES: Record<string, LucideIcon> = {
  projeto_criado: BookOpen,
  projeto_editado: Pencil,
  projeto_excluido: Trash2,
  documento_enviado: FileText,
  documento_excluido: Trash2,
  conversa_excluida: MessageSquare,
  projeto_renomeado: Pencil,
}
function formatarDataCurta(iso: string) {
  const partes = new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
  }).formatToParts(new Date(iso))
  const dia = partes.find((p) => p.type === "day")?.value
  const mes = partes.find((p) => p.type === "month")?.value.replace(".", "")
  return `${dia} ${mes}.`
}

export default function AtividadesRecentes() {
  const [itens, setItens] = useState<Atividade[] | null>(null)

  useEffect(() => {
    fetch("http://localhost:8000/api/atividades/recentes/?limite=5", {
      credentials: "include",
    })
      .then((res) => (res.ok ? res.json() : []))
      .then(setItens)
      .catch(() => setItens([]))
  }, [])

  return (
    <section className="rounded-xl bg-[var(--surface-elevated)] p-6 border border-gray-800/40">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider">
          Atividades Recentes
        </h2>

        <button
          type="button"
          className="text-sm font-medium text-orange-500 hover:text-orange-400 transition-colors"
        >
          Ver tudo
        </button>
      </div>

      {itens === null && (
        <p className="text-sm text-gray-400 py-4">Carregando atividades...</p>
      )}

      {itens?.length === 0 && (
        <p className="text-sm text-gray-400 py-6 text-center">
          Nenhuma atividade registrada até o momento.
        </p>
      )}

      {itens && itens.length > 0 && (
        <ul className="flex flex-col">
          {itens.map((a, index) => {
            const Icone = ICONES[a.acao] ?? Activity
            return (
              <li
                key={a.id}
                className={`flex items-center gap-4 py-3.5 ${
                  index !== itens.length - 1
                    ? "border-b border-orange-200/70"
                    : ""
                }`}
              >
                <div className="flex items-center justify-center w-8 h-8 shrink-0 rounded-full bg-[var(--primary)]">
                  <Icone
                    size={16}
                    className="text-[var(--background)] font-bold"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200 leading-relaxed">
                    <span className="font-semibold text-white">
                      {a.usuario}
                    </span>{" "}
                    {a.texto}
                    {a.alvo && (
                      <span className="font-semibold text-orange-500">
                        {" "}
                        {a.alvo}
                      </span>
                    )}
                    {a.acao === "projeto_renomeado" && a.detalhe && (
                      <>
                        {" para "}
                        <span className="font-semibold text-orange-500">
                          {a.detalhe}
                        </span>
                      </>
                    )}
                  </p>
                </div>

                <span className="text-xs text-gray-400 shrink-0 whitespace-nowrap">
                  {formatarDataCurta(a.criado_em)}
                </span>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
