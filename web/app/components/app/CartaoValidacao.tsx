import { CircleCheck, CircleX, TriangleAlert } from "lucide-react"

export type PendenciaCartao = {
  regra: string
  nivel: string
  item: string
  mensagem: string
}

export type Validacao = {
  conforme: boolean
  total_regras: number
  aprovadas: number
  erros: PendenciaCartao[]
  avisos: PendenciaCartao[]
  observacoes: string[]
}

function LinhaPendencia({ p, cor }: { p: PendenciaCartao; cor: string }) {
  return (
    <li className="rounded-lg bg-black/20 px-3 py-2">
      <div className="flex flex-wrap items-center gap-2">
        <code className={`text-[11px] font-semibold ${cor}`}>{p.regra}</code>
        <span className="text-[11px] text-(--foreground-muted)">
          {p.nivel} · {p.item}
        </span>
      </div>
      <p className="mt-1 text-xs text-gray-200">{p.mensagem}</p>
    </li>
  )
}

export default function CartaoValidacao({
  validacao,
}: {
  validacao: Validacao
}) {
  const { conforme, erros, avisos, aprovadas, total_regras, observacoes } =
    validacao

  return (
    <div
      className={`mb-3 rounded-xl border p-4 ${
        conforme
          ? "border-green-500/40 bg-green-500/5"
          : "border-red-500/40 bg-red-500/5"
      }`}
    >
      <div className="flex items-start gap-3">
        {conforme ? (
          <CircleCheck size={22} className="mt-0.5 shrink-0 text-green-400" />
        ) : (
          <CircleX size={22} className="mt-0.5 shrink-0 text-red-400" />
        )}
        <div>
          <p className="text-sm font-semibold text-white">
            {conforme
              ? "Especificação em conformidade"
              : "Pendências encontradas"}
          </p>
          <p className="text-xs text-(--foreground-muted)">
            {erros.length} erro(s) · {avisos.length} aviso(s) · {aprovadas} de{" "}
            {total_regras} regras aprovadas
          </p>
        </div>
      </div>

      {erros.length > 0 && (
        <div className="mt-3">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-red-400">
            <CircleX size={14} /> Erros
          </p>
          <ul className="flex flex-col gap-2">
            {erros.map((p, i) => (
              <LinhaPendencia
                key={`${p.regra}-${i}`}
                p={p}
                cor="text-red-400"
              />
            ))}
          </ul>
        </div>
      )}

      {avisos.length > 0 && (
        <details open={erros.length === 0} className="mt-3">
          <summary className="mb-2 flex cursor-pointer items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-amber-400">
            <TriangleAlert size={14} /> Avisos ({avisos.length})
          </summary>
          <ul className="flex flex-col gap-2">
            {avisos.map((p, i) => (
              <LinhaPendencia
                key={`${p.regra}-${i}`}
                p={p}
                cor="text-amber-400"
              />
            ))}
          </ul>
        </details>
      )}

      {observacoes.length > 0 && (
        <ul className="mt-3 list-disc pl-5 text-xs text-(--foreground-muted)">
          {observacoes.map((o, i) => (
            <li key={i}>{o}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
