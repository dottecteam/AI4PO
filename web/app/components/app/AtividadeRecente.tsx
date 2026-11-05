"use client"
import { useEffect, useState } from "react"

type Atividade = {
  id: number
  usuario: string
  texto: string
  alvo: string
  criado_em: string
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
    <section className="rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-(--foreground-muted) mb-3">
        Atividade recente
      </h2>

      {itens === null && (
        <p className="text-sm text-(--foreground-muted)">Carregando...</p>
      )}
      {itens?.length === 0 && (
        <p className="text-sm text-(--foreground-muted)">
          Nenhuma atividade ainda.
        </p>
      )}

      <ul className="flex flex-col gap-2">
        {itens?.map((a) => (
          <li key={a.id} className="text-sm text-gray-300">
            <span className="font-medium text-white">{a.usuario}</span>{" "}
            {a.texto}
            {a.alvo && <> “{a.alvo}”</>}
            <span className="text-(--foreground-muted)">
              {" "}
              - {formatarDataCurta(a.criado_em)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
