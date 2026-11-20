"use client"

import Link from "next/link"
import { BriefcaseBusiness, FolderOpen, Sparkles } from "lucide-react"
import type { ProjetoStatus } from "@/app/types/api/projeto"
import type { ParticipacaoPerfil, PerfilProfissional } from "@/app/types/api/profissional"

const statusColors: Record<ProjetoStatus, string> = {
  Rascunho: "bg-[#f4be63] text-[#9a6500]",
  Inativo: "bg-[#f6b3ad] text-[#8f3f38]",
  Ativo: "bg-[#ecfda5] text-[#526300]",
}

type ProjetoAgrupado = {
  projeto: ParticipacaoPerfil["projeto"]
  papeis: ParticipacaoPerfil[]
}

// Agrupa as participações por projeto, mantendo a ordem (mais recente primeiro)
function agruparPorProjeto(participacoes: ParticipacaoPerfil[]): ProjetoAgrupado[] {
  const grupos = new Map<number, ProjetoAgrupado>()
  for (const participacao of participacoes) {
    const grupo = grupos.get(participacao.projeto.id)
    if (grupo) grupo.papeis.push(participacao)
    else grupos.set(participacao.projeto.id, { projeto: participacao.projeto, papeis: [participacao] })
  }
  return [...grupos.values()]
}

function formatarData(iso: string) {
  return new Date(iso).toLocaleDateString("pt-BR")
}

type Props = {
  perfil: PerfilProfissional
}

export default function TrajetoriaProfissional({ perfil }: Props) {
  const projetos = agruparPorProjeto(perfil.participacoes)
  const totalPapeis = new Set(perfil.participacoes.map((p) => p.papel.toLowerCase())).size

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Indicador icone={<FolderOpen size={19} />} rotulo="Projetos" valor={projetos.length} />
        <Indicador icone={<BriefcaseBusiness size={19} />} rotulo="Papéis desempenhados" valor={totalPapeis} />
        <Indicador icone={<Sparkles size={19} />} rotulo="Competências" valor={perfil.competencias.length} />
      </div>

      <section aria-label="Competências" className="flex flex-col gap-3">
        <div>
          <h3 className="text-white font-semibold text-base">Competências</h3>
          <p className="text-secondary text-xs mt-1">Conhecimentos técnicos do profissional.</p>
        </div>

        {perfil.competencias.length === 0 ? (
          <p className="text-secondary text-sm rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4">
            Nenhuma competência cadastrada.
          </p>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {perfil.competencias.map((competencia) => (
              <li
                key={competencia.id}
                className="rounded-full bg-primary/10 border border-primary/20 px-3 py-1 text-xs font-medium text-primary"
              >
                {competencia.nome}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-label="Projetos e papéis" className="flex flex-col gap-3">
        <div>
          <h3 className="text-white font-semibold text-base">Projetos e papéis</h3>
          <p className="text-secondary text-xs mt-1">Trajetória do profissional nos projetos da plataforma.</p>
        </div>

        {projetos.length === 0 ? (
          <p className="text-secondary text-sm rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4">
            Nenhuma participação em projetos registrada.
          </p>
        ) : (
          <ul className="flex flex-col gap-3">
            {projetos.map(({ projeto, papeis }) => (
              <li
                key={projeto.id}
                className="rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4 flex flex-col gap-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Link
                    href={`/projetos/${projeto.id}`}
                    className="text-white text-sm font-semibold hover:text-primary transition-colors break-words"
                  >
                    {projeto.titulo}
                  </Link>
                  <span className={`rounded px-2 py-0.5 text-xs font-bold ${statusColors[projeto.status]}`}>
                    {projeto.status}
                  </span>
                </div>

                <ul className="flex flex-col divide-y divide-gray-800/50">
                  {papeis.map((participacao) => (
                    <li key={participacao.id} className="flex items-center justify-between gap-3 py-2 first:pt-0 last:pb-0">
                      <span className="text-sm text-white break-words">{participacao.papel}</span>
                      <span className="text-xs text-secondary shrink-0">
                        Desde {formatarData(participacao.criado_em)}
                      </span>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

function Indicador({ icone, rotulo, valor }: { icone: React.ReactNode; rotulo: string; valor: number }) {
  return (
    <div className="rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4 flex items-center gap-4">
      <div className="h-10 w-10 shrink-0 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
        {icone}
      </div>
      <div className="flex flex-col gap-0.5">
        <span className="text-secondary text-xs">{rotulo}</span>
        <span className="text-white text-lg font-semibold">{valor}</span>
      </div>
    </div>
  )
}
