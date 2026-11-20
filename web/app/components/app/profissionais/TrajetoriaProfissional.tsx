"use client"

import { useState } from "react"
import Link from "next/link"
import { BriefcaseBusiness, FolderOpen, Pencil, Plus, Sparkles, Trash2 } from "lucide-react"
import ParticipacaoModal from "./ParticipacaoModal"
import { mensagemDaApi, participacaoService } from "@/app/services/API/ProfissionalService"
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
  // Quando informado, habilita adicionar/editar/excluir participações (Task #15-3).
  // Os botões só aparecem para o PO do projeto ou para o administrador.
  onAlterado?: () => void
}

type Edicao = { participacao?: ParticipacaoPerfil }

export default function TrajetoriaProfissional({ perfil, onAlterado }: Props) {
  const [edicao, setEdicao] = useState<Edicao | null>(null)
  const [excluindo, setExcluindo] = useState<ParticipacaoPerfil | null>(null)
  const [processando, setProcessando] = useState(false)
  const [erroExclusao, setErroExclusao] = useState("")

  const gerenciavel = !!onAlterado
  const podeAdicionar = gerenciavel && perfil.projetos_gerenciaveis.length > 0

  const confirmarExclusao = async () => {
    if (!excluindo || processando) return
    setProcessando(true)
    setErroExclusao("")
    try {
      await participacaoService.excluir(excluindo.id)
      setExcluindo(null)
      onAlterado?.()
    } catch (e) {
      setErroExclusao(mensagemDaApi(e, "Não foi possível excluir a participação."))
    } finally {
      setProcessando(false)
    }
  }

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
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h3 className="text-white font-semibold text-base">Projetos e papéis</h3>
            <p className="text-secondary text-xs mt-1">Trajetória do profissional nos projetos da plataforma.</p>
          </div>
          {podeAdicionar && (
            <button
              type="button"
              onClick={() => setEdicao({})}
              className="h-9 px-3 rounded-lg flex items-center gap-1.5 text-sm font-medium text-white bg-primary hover:bg-primary-dark transition-colors cursor-pointer"
            >
              <Plus size={16} />
              Adicionar participação
            </button>
          )}
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
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs text-secondary">
                          Desde {formatarData(participacao.criado_em)}
                        </span>
                        {gerenciavel && participacao.pode_editar && (
                          <>
                            <button
                              type="button"
                              onClick={() => setEdicao({ participacao })}
                              aria-label={`Editar papel ${participacao.papel} em ${projeto.titulo}`}
                              title="Editar"
                              className="p-1.5 rounded-md text-secondary hover:text-white hover:bg-(--surface-base) transition-colors cursor-pointer"
                            >
                              <Pencil size={14} />
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setErroExclusao("")
                                setExcluindo(participacao)
                              }}
                              aria-label={`Excluir papel ${participacao.papel} em ${projeto.titulo}`}
                              title="Excluir"
                              className="p-1.5 rounded-md text-secondary hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                            >
                              <Trash2 size={14} />
                            </button>
                          </>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </section>

      {edicao && onAlterado && (
        <ParticipacaoModal
          funcionarioId={perfil.id}
          nomeProfissional={perfil.nome}
          projetos={perfil.projetos_gerenciaveis}
          participacao={edicao.participacao}
          onFechar={() => setEdicao(null)}
          onSalvo={() => {
            setEdicao(null)
            onAlterado()
          }}
        />
      )}

      {excluindo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="titulo-excluir-participacao"
            className="w-full max-w-md bg-(--surface-base) border border-gray-800/50 rounded-2xl p-6 flex flex-col gap-4 shadow-2xl"
          >
            <div className="flex flex-col gap-1">
              <h2 id="titulo-excluir-participacao" className="text-white text-lg font-semibold">
                Excluir participação?
              </h2>
              <p className="text-secondary text-sm">
                {perfil.nome} deixará de constar como &ldquo;{excluindo.papel}&rdquo; em{" "}
                {excluindo.projeto.titulo}. Essa ação não pode ser desfeita.
              </p>
            </div>

            {erroExclusao && (
              <p role="alert" className="text-sm text-red-300">
                {erroExclusao}
              </p>
            )}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setExcluindo(null)}
                disabled={processando}
                className="h-10 px-4 rounded-lg text-sm text-white border border-gray-700/50 hover:bg-(--surface-elevated) transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={confirmarExclusao}
                disabled={processando}
                className="h-10 px-4 rounded-lg text-sm font-medium text-white bg-red-600 hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {processando ? "Excluindo..." : "Excluir"}
              </button>
            </div>
          </div>
        </div>
      )}
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
