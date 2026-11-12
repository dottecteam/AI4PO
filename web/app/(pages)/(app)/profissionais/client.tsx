"use client"

import { useEffect, useState } from "react"
import { Plus, RefreshCw, Search, X } from "lucide-react"
import {
  buscarProfissionais,
  listarCompetencias,
  listarProfissionais,
} from "@/app/services/API/profissionais"
import { encerrarSessao, mensagemDeErro, sessaoInvalida } from "@/app/services/API/usuarios"
import type {
  CompetenciaResumo,
  Profissional,
  ProfissionalAfinidade,
  ResultadoBusca,
} from "@/app/types/api/profissional"
import CadastroProfissionalModal from "./CadastroProfissionalModal"
import SeletorCompetencias from "./SeletorCompetencias"

// 66.7 -> "66,7%"
const percentual = (valor: number) => `${valor.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`

const porNome = (a: { nome: string }, b: { nome: string }) => a.nome.localeCompare(b.nome, "pt-BR")

function Chips({ itens, estilo }: { itens: CompetenciaResumo[]; estilo: "possui" | "falta" | "neutro" }) {
  const classes = {
    possui: "bg-green-500/15 text-green-400",
    falta: "bg-(--surface-base) text-secondary border border-dashed border-gray-700/60",
    neutro: "bg-(--surface-base) text-white border border-gray-700/50",
  }[estilo]
  return (
    <>
      {itens.map((c) => (
        <span key={c.id} className={`px-2.5 py-1 rounded-full text-xs font-medium ${classes}`}>
          {c.nome}
        </span>
      ))}
    </>
  )
}

function CartaoResultado({
  profissional: p,
  posicao,
  totalBuscadas,
}: {
  profissional: ProfissionalAfinidade
  posicao: number
  totalBuscadas: number
}) {
  return (
    <li className="bg-(--surface-elevated) border border-gray-800/50 rounded-xl p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <span
            aria-label={`Posição ${posicao}`}
            className="h-8 w-8 shrink-0 rounded-full bg-primary/15 text-primary text-sm font-semibold flex items-center justify-center"
          >
            {posicao}
          </span>
          <div className="flex flex-col min-w-0">
            <span className="text-white text-sm sm:text-base font-medium truncate">{p.nome}</span>
            <span className="text-secondary text-xs sm:text-sm truncate">{p.email}</span>
          </div>
        </div>
        <div className="flex flex-col items-end shrink-0">
          <span className="text-white text-lg font-semibold">{percentual(p.afinidade)}</span>
          <span className="text-secondary text-xs">afinidade</span>
        </div>
      </div>

      <div
        role="progressbar"
        aria-label={`Afinidade de ${p.nome}`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={p.afinidade}
        className="h-1.5 w-full rounded-full bg-(--surface-base) overflow-hidden"
      >
        <div className="h-full bg-primary" style={{ width: `${p.afinidade}%` }} />
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-secondary">
        <span>
          {p.competencias_correspondentes.length} de {totalBuscadas} competências buscadas
        </span>
        <span>Foco: {percentual(p.foco)}</span>
        <span>{p.total_competencias} competências no total</span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {p.competencias_correspondentes.length > 0 && <span className="text-xs text-secondary">Possui:</span>}
        <Chips itens={p.competencias_correspondentes} estilo="possui" />
        {p.competencias_faltantes.length > 0 && <span className="text-xs text-secondary ml-1">Falta:</span>}
        <Chips itens={p.competencias_faltantes} estilo="falta" />
      </div>
    </li>
  )
}

function Profissionais() {
  const [competencias, setCompetencias] = useState<CompetenciaResumo[]>([])
  const [profissionais, setProfissionais] = useState<Profissional[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [recarga, setRecarga] = useState(0)

  const [selecionadas, setSelecionadas] = useState<number[]>([])
  const [resultado, setResultado] = useState<ResultadoBusca | null>(null)
  const [idsBuscados, setIdsBuscados] = useState<number[]>([])
  const [buscando, setBuscando] = useState(false)
  const [erroBusca, setErroBusca] = useState("")

  const [cadastrando, setCadastrando] = useState(false)
  const [aviso, setAviso] = useState("")

  // Catálogo de competências e listagem inicial
  useEffect(() => {
    let ativo = true

    Promise.all([listarCompetencias(), listarProfissionais()])
      .then(([catalogo, lista]) => {
        if (!ativo) return
        setCompetencias(catalogo)
        setProfissionais(lista)
        setErro("")
        setCarregando(false)
      })
      .catch((e) => {
        if (sessaoInvalida(e)) {
          encerrarSessao()
          return
        }
        if (!ativo) return
        setErro(mensagemDeErro(e))
        setCarregando(false)
      })

    return () => {
      ativo = false
    }
  }, [recarga])

  const recarregar = () => {
    setCarregando(true)
    setAviso("")
    setRecarga((n) => n + 1)
  }

  const executarBusca = async (ids: number[]) => {
    setBuscando(true)
    setErroBusca("")
    try {
      const encontrado = await buscarProfissionais(ids)
      setResultado(encontrado)
      setIdsBuscados(ids)
    } catch (e) {
      if (sessaoInvalida(e)) {
        encerrarSessao()
        return
      }
      setErroBusca(mensagemDeErro(e))
    } finally {
      setBuscando(false)
    }
  }

  const limpar = () => {
    setSelecionadas([])
    setResultado(null)
    setIdsBuscados([])
    setErroBusca("")
  }

  const abrirCadastro = () => {
    setAviso("")
    setCadastrando(true)
  }

  const aoCadastrar = (novo: Profissional) => {
    setProfissionais((prev) => [...prev, novo].sort(porNome))
    setAviso(`Profissional ${novo.nome} cadastrado.`)
    setCadastrando(false)
    // Se há uma busca na tela, o novo profissional pode entrar nela: refaz com as mesmas competências
    if (resultado) void executarBusca(idsBuscados)
  }

  return (
    <div className="w-full h-full flex flex-col flex-1 bg-background">

      {/* Cabeçalho */}
      <div className="w-full shrink-0 flex justify-between items-center gap-4 px-4 sm:px-6 lg:px-8 py-4 bg-background border-b border-gray-800/50 z-10">
        <div className="flex flex-col gap-1 min-w-0">
          <h1 className="text-white font-semibold text-lg sm:text-2xl lg:text-3xl truncate">Profissionais</h1>
          <span className="text-secondary text-xs sm:text-sm">
            Busque por competência e veja quem tem mais afinidade
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={abrirCadastro}
            disabled={carregando || !!erro}
            aria-label="Novo profissional"
            title="Novo profissional"
            className="h-10 px-3 sm:px-4 bg-primary hover:bg-primary-dark rounded-lg flex items-center justify-center gap-2 text-sm font-medium text-white transition-colors disabled:opacity-50"
          >
            <Plus size={18} />
            <span className="hidden sm:inline">Novo profissional</span>
          </button>
          <button
            type="button"
            onClick={recarregar}
            disabled={carregando}
            aria-label="Atualizar lista"
            className="h-10 w-10 shrink-0 bg-(--surface-elevated) rounded-lg flex items-center justify-center border border-gray-800/50 hover:bg-(--surface-base) transition-colors disabled:opacity-50"
          >
            <RefreshCw size={18} className={`text-white ${carregando ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Conteúdo */}
      <div className="w-full flex-1 min-h-0 overflow-y-auto flex flex-col gap-5 px-4 sm:px-6 lg:px-8 py-6">

        {/* Aviso de sucesso */}
        {aviso && (
          <div
            role="status"
            className="flex items-start justify-between gap-3 rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-300"
          >
            <span>{aviso}</span>
            <button type="button" onClick={() => setAviso("")} aria-label="Fechar aviso" className="shrink-0 text-green-300 hover:text-white">
              <X size={16} />
            </button>
          </div>
        )}

        {carregando && <div className="text-secondary text-sm animate-pulse">Carregando profissionais...</div>}

        {!carregando && erro && (
          <div role="alert" className="flex flex-col items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            <span>{erro}</span>
            <button
              type="button"
              onClick={recarregar}
              className="h-9 px-4 rounded-lg bg-(--surface-elevated) text-white border border-gray-800/50 hover:bg-(--surface-base) transition-colors"
            >
              Tentar de novo
            </button>
          </div>
        )}

        {!carregando && !erro && (
          <>
            {/* Busca por competência */}
            <section
              aria-label="Buscar por competência"
              className="bg-(--surface-elevated) border border-gray-800/50 rounded-xl p-4 flex flex-col gap-3"
            >
              <h2 className="text-white text-sm font-semibold">Buscar por competência</h2>

              {competencias.length === 0 ? (
                <p className="text-sm text-secondary">Nenhuma competência cadastrada ainda.</p>
              ) : (
                <SeletorCompetencias
                  rotulo="Competências buscadas"
                  competencias={competencias}
                  selecionadas={selecionadas}
                  onAlterar={setSelecionadas}
                  desabilitado={buscando}
                />
              )}

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => executarBusca(selecionadas)}
                  disabled={selecionadas.length === 0 || buscando}
                  className="h-10 px-4 rounded-lg flex items-center gap-2 text-sm font-medium text-white bg-primary hover:bg-primary-dark transition-colors disabled:opacity-50"
                >
                  <Search size={16} />
                  {buscando ? "Buscando..." : "Buscar"}
                </button>
                {(selecionadas.length > 0 || resultado) && (
                  <button
                    type="button"
                    onClick={limpar}
                    disabled={buscando}
                    className="h-10 px-4 rounded-lg text-sm text-white border border-gray-700/50 hover:bg-(--surface-base) transition-colors disabled:opacity-50"
                  >
                    Limpar
                  </button>
                )}
              </div>

              {erroBusca && (
                <p role="alert" className="text-sm text-red-300">
                  {erroBusca}
                </p>
              )}
            </section>

            {/* Resultado da busca, com os critérios de afinidade */}
            {resultado && (
              <>
                <section
                  aria-label="Critérios de afinidade"
                  className="bg-(--surface-elevated) border border-gray-800/50 rounded-xl p-4 flex flex-col gap-3"
                >
                  <h2 className="text-white text-sm font-semibold">Critérios de afinidade</h2>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs text-secondary">Competências buscadas:</span>
                    <Chips itens={resultado.criterios.competencias_buscadas} estilo="neutro" />
                  </div>
                  <p className="text-sm text-secondary">{resultado.criterios.afinidade}</p>
                  <div className="flex flex-col gap-1">
                    <span className="text-xs text-secondary">Ordem dos resultados:</span>
                    <ol className="flex flex-col gap-1 text-sm text-secondary list-decimal pl-5">
                      {resultado.criterios.ordenacao.map((regra) => (
                        <li key={regra}>{regra.replace(/^\d+º\s*/, "")}</li>
                      ))}
                    </ol>
                  </div>
                </section>

                <section aria-label="Resultados da busca" className="flex flex-col gap-3">
                  <span className="text-secondary text-sm">
                    {resultado.total === 0
                      ? "Nenhum profissional tem as competências buscadas."
                      : `${resultado.total} ${resultado.total === 1 ? "profissional encontrado" : "profissionais encontrados"}`}
                  </span>
                  {resultado.total > 0 && (
                    <ol className="flex flex-col gap-2">
                      {resultado.resultados.map((p, i) => (
                        <CartaoResultado
                          key={p.id}
                          profissional={p}
                          posicao={i + 1}
                          totalBuscadas={resultado.criterios.competencias_buscadas.length}
                        />
                      ))}
                    </ol>
                  )}
                </section>
              </>
            )}

            {/* Listagem geral (quando não há busca na tela) */}
            {!resultado && (
              <section aria-label="Todos os profissionais" className="flex flex-col gap-3">
                <span className="text-secondary text-sm">
                  {profissionais.length === 0
                    ? "Nenhum profissional cadastrado ainda."
                    : `${profissionais.length} ${profissionais.length === 1 ? "profissional" : "profissionais"}`}
                </span>
                {profissionais.length > 0 && (
                  <ul className="flex flex-col gap-2">
                    {profissionais.map((p) => (
                      <li
                        key={p.id}
                        className="bg-(--surface-elevated) border border-gray-800/50 rounded-xl px-4 py-3 flex flex-col gap-2"
                      >
                        <div className="flex flex-col min-w-0">
                          <span className="text-white text-sm sm:text-base font-medium truncate">{p.nome}</span>
                          <span className="text-secondary text-xs sm:text-sm truncate">{p.email}</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Chips itens={p.competencias} estilo="neutro" />
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}
          </>
        )}
      </div>

      {/* Cadastro */}
      {cadastrando && (
        <CadastroProfissionalModal
          competencias={competencias}
          onFechar={() => setCadastrando(false)}
          onCriado={aoCadastrar}
        />
      )}
    </div>
  )
}

export default Profissionais