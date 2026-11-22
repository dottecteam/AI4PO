"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { Pencil, Plus, Search, Trash2, Users } from "lucide-react"
import { useAuth } from "@/app/contexts/AuthContext"
import {
  buscarProfissionais,
  excluirCompetencia,
  listarCompetenciasComTotais,
} from "@/app/services/API/profissionais"
import { encerrarSessao, mensagemDeErro, sessaoInvalida } from "@/app/services/API/usuarios"
import type { CompetenciaGerenciada, ProfissionalAfinidade } from "@/app/types/api/profissional"
import CompetenciaModal from "./CompetenciaModal"

const porNome = (a: { nome: string }, b: { nome: string }) => a.nome.localeCompare(b.nome, "pt-BR")

// 66.7 -> "66,7%"
const percentual = (valor: number) => `${valor.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`

type Edicao = { alvo?: CompetenciaGerenciada }

export default function Competencias() {
  const { usuario } = useAuth()
  const ehAdmin = !!usuario?.is_admin

  const [competencias, setCompetencias] = useState<CompetenciaGerenciada[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [filtro, setFiltro] = useState("")
  const [aviso, setAviso] = useState("")

  const [selecionada, setSelecionada] = useState<CompetenciaGerenciada | null>(null)
  const [ranking, setRanking] = useState<ProfissionalAfinidade[] | null>(null)
  const [erroRanking, setErroRanking] = useState("")

  const [edicao, setEdicao] = useState<Edicao | null>(null)
  const [excluindo, setExcluindo] = useState<CompetenciaGerenciada | null>(null)
  const [processando, setProcessando] = useState(false)
  const [erroExclusao, setErroExclusao] = useState("")

  useEffect(() => {
    let ativo = true
    listarCompetenciasComTotais()
      .then((lista) => {
        if (!ativo) return
        setCompetencias(lista)
        setErro("")
      })
      .catch((e) => {
        if (sessaoInvalida(e)) return encerrarSessao()
        if (ativo) setErro(mensagemDeErro(e))
      })
      .finally(() => {
        if (ativo) setCarregando(false)
      })
    return () => {
      ativo = false
    }
  }, [])

  // Quem melhor se encaixa na competência escolhida (mesma regra de afinidade da busca de profissionais)
  useEffect(() => {
    if (!selecionada || selecionada.total_profissionais === 0) return
    let ativo = true
    buscarProfissionais([selecionada.id])
      .then((r) => {
        if (!ativo) return
        setRanking(r.resultados)
        setErroRanking("")
      })
      .catch((e) => {
        if (sessaoInvalida(e)) return encerrarSessao()
        if (ativo) setErroRanking(mensagemDeErro(e))
      })
    return () => {
      ativo = false
    }
  }, [selecionada])

  const visiveis = useMemo(() => {
    const termo = filtro.trim().toLowerCase()
    return termo ? competencias.filter((c) => c.nome.toLowerCase().includes(termo)) : competencias
  }, [competencias, filtro])

  const totalVinculos = competencias.reduce((soma, c) => soma + c.total_profissionais, 0)
  const semProfissionais = competencias.filter((c) => c.total_profissionais === 0).length

  const selecionar = (competencia: CompetenciaGerenciada) => {
    setRanking(competencia.total_profissionais === 0 ? [] : null)
    setErroRanking("")
    setSelecionada(competencia)
  }

  const aoSalvar = (salva: CompetenciaGerenciada) => {
    const nova = !competencias.some((c) => c.id === salva.id)
    setCompetencias((lista) =>
      (nova ? [...lista, salva] : lista.map((c) => (c.id === salva.id ? salva : c))).sort(porNome),
    )
    if (selecionada?.id === salva.id) setSelecionada(salva)
    setAviso(nova ? `Competência "${salva.nome}" cadastrada.` : `Competência renomeada para "${salva.nome}".`)
    setEdicao(null)
  }

  const confirmarExclusao = async () => {
    if (!excluindo || processando) return
    setProcessando(true)
    setErroExclusao("")
    try {
      await excluirCompetencia(excluindo.id)
      setCompetencias((lista) => lista.filter((c) => c.id !== excluindo.id))
      if (selecionada?.id === excluindo.id) setSelecionada(null)
      setAviso(`Competência "${excluindo.nome}" excluída.`)
      setExcluindo(null)
    } catch (e) {
      if (sessaoInvalida(e)) return encerrarSessao()
      setErroExclusao(mensagemDeErro(e))
    } finally {
      setProcessando(false)
    }
  }

  return (
    <div className="w-full h-full flex flex-col flex-1 bg-background">
      <header className="w-full shrink-0 px-4 sm:px-6 lg:px-8 py-4 border-b border-gray-800/50 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-white font-semibold text-lg sm:text-2xl">Competências</h1>
          <p className="text-secondary text-xs sm:text-sm mt-1">
            Gerencie o catálogo e veja quais profissionais melhor se encaixam em cada competência.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setAviso("")
            setEdicao({})
          }}
          className="h-10 px-4 rounded-lg flex items-center gap-2 text-sm font-medium text-white bg-primary hover:bg-primary-dark transition-colors cursor-pointer"
        >
          <Plus size={16} />
          Nova competência
        </button>
      </header>

      <main className="w-full flex-1 min-h-0 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">
        {aviso && (
          <p role="status" className="text-sm text-green-400 rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-2">
            {aviso}
          </p>
        )}

        {erro ? (
          <p role="alert" className="text-sm text-red-300">{erro}</p>
        ) : carregando ? (
          <p className="text-secondary text-sm">Carregando...</p>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Indicador rotulo="Competências cadastradas" valor={competencias.length} />
              <Indicador rotulo="Vínculos com profissionais" valor={totalVinculos} />
              <Indicador rotulo="Sem nenhum profissional" valor={semProfissionais} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-6 items-start">
              {/* Catálogo */}
              <section aria-label="Catálogo de competências" className="flex flex-col gap-3 min-w-0">
                <label className="flex items-center w-full rounded-lg border border-gray-700/50 bg-(--surface-base) focus-within:border-primary transition-colors">
                  <Search size={16} className="ml-3 shrink-0 text-primary" />
                  <span className="sr-only">Filtrar competências</span>
                  <input
                    type="text"
                    value={filtro}
                    onChange={(e) => setFiltro(e.target.value)}
                    placeholder="Filtrar competências"
                    className="w-full px-3 py-2 text-sm text-white bg-transparent outline-none"
                  />
                </label>

                {visiveis.length === 0 ? (
                  <p className="text-secondary text-sm">
                    {competencias.length === 0 ? "Nenhuma competência cadastrada ainda." : "Nenhuma competência encontrada."}
                  </p>
                ) : (
                  <ul className="flex flex-col gap-2">
                    {visiveis.map((c) => {
                      const ativa = selecionada?.id === c.id
                      return (
                        <li
                          key={c.id}
                          className={`rounded-xl border px-4 py-3 flex items-center gap-3 transition-colors ${
                            ativa
                              ? "border-primary bg-primary/10"
                              : "border-gray-800/50 bg-(--surface-elevated) hover:border-gray-600"
                          }`}
                        >
                          <button
                            type="button"
                            onClick={() => selecionar(c)}
                            aria-pressed={ativa}
                            className="flex-1 min-w-0 text-left flex flex-col cursor-pointer"
                          >
                            <span className="text-white text-sm font-medium truncate">{c.nome}</span>
                            <span className="text-secondary text-xs flex items-center gap-1">
                              <Users size={12} />
                              {c.total_profissionais === 1 ? "1 profissional" : `${c.total_profissionais} profissionais`}
                            </span>
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setAviso("")
                              setEdicao({ alvo: c })
                            }}
                            aria-label={`Renomear ${c.nome}`}
                            title="Renomear"
                            className="p-1.5 rounded-md text-secondary hover:text-white hover:bg-(--surface-base) transition-colors cursor-pointer"
                          >
                            <Pencil size={15} />
                          </button>
                          {ehAdmin && (
                            <button
                              type="button"
                              onClick={() => {
                                setAviso("")
                                setErroExclusao("")
                                setExcluindo(c)
                              }}
                              aria-label={`Excluir ${c.nome}`}
                              title="Excluir"
                              className="p-1.5 rounded-md text-secondary hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                            >
                              <Trash2 size={15} />
                            </button>
                          )}
                        </li>
                      )
                    })}
                  </ul>
                )}
              </section>

              {/* Quem melhor se encaixa */}
              <section
                aria-label="Profissionais da competência"
                aria-live="polite"
                className="rounded-2xl border border-gray-800/50 bg-(--surface-elevated) p-4 sm:p-5 flex flex-col gap-4 lg:sticky lg:top-0"
              >
                {!selecionada ? (
                  <p className="text-secondary text-sm">
                    Selecione uma competência para ver quais profissionais melhor se encaixam nela.
                  </p>
                ) : (
                  <>
                    <div>
                      <h2 className="text-white font-semibold text-base">{selecionada.nome}</h2>
                      <p className="text-secondary text-xs mt-1">
                        Ordenado pelo foco: quem tem menos competências fora desta aparece primeiro.
                      </p>
                    </div>

                    {erroRanking ? (
                      <p role="alert" className="text-sm text-red-300">{erroRanking}</p>
                    ) : ranking === null ? (
                      <p className="text-secondary text-sm">Carregando...</p>
                    ) : ranking.length === 0 ? (
                      <p className="text-secondary text-sm">
                        Nenhum profissional tem esta competência ainda. Vincule-a pelo cadastro em{" "}
                        <Link href="/profissionais" className="text-primary hover:underline">Profissionais</Link>.
                      </p>
                    ) : (
                      <ol className="flex flex-col gap-2">
                        {ranking.map((p, i) => (
                          <li
                            key={p.id}
                            className="rounded-xl bg-(--surface-base) border border-gray-800/50 px-3 py-2.5 flex items-center gap-3"
                          >
                            <span className="h-7 w-7 shrink-0 rounded-full bg-primary/15 text-primary text-xs font-semibold flex items-center justify-center">
                              {i + 1}
                            </span>
                            <div className="flex-1 min-w-0">
                              <Link
                                href={`/profissionais/${p.id}`}
                                className="block text-white text-sm font-medium truncate hover:text-primary transition-colors"
                              >
                                {p.nome}
                              </Link>
                              <span className="text-secondary text-xs">
                                {p.total_competencias} competências no total
                              </span>
                            </div>
                            <div className="flex flex-col items-end shrink-0">
                              <span className="text-white text-sm font-semibold">{percentual(p.foco)}</span>
                              <span className="text-secondary text-[11px]">foco</span>
                            </div>
                          </li>
                        ))}
                      </ol>
                    )}
                  </>
                )}
              </section>
            </div>
          </>
        )}
      </main>

      {edicao && <CompetenciaModal alvo={edicao.alvo} onFechar={() => setEdicao(null)} onSalvo={aoSalvar} />}

      {excluindo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="titulo-excluir-competencia"
            className="w-full max-w-md bg-(--surface-base) border border-gray-800/50 rounded-2xl p-6 flex flex-col gap-4 shadow-2xl"
          >
            <div className="flex flex-col gap-1">
              <h2 id="titulo-excluir-competencia" className="text-white text-lg font-semibold">
                Excluir competência?
              </h2>
              <p className="text-secondary text-sm">
                &ldquo;{excluindo.nome}&rdquo; será removida do catálogo
                {excluindo.total_profissionais > 0
                  ? ` e de ${excluindo.total_profissionais} profissional(is) que a possuem`
                  : ""}
                . Essa ação não pode ser desfeita.
              </p>
            </div>
            {erroExclusao && (
              <p role="alert" className="text-sm text-red-300">{erroExclusao}</p>
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

function Indicador({ rotulo, valor }: { rotulo: string; valor: number }) {
  return (
    <div className="rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4 flex flex-col gap-0.5">
      <span className="text-secondary text-xs">{rotulo}</span>
      <span className="text-white text-xl font-semibold">{valor}</span>
    </div>
  )
}
