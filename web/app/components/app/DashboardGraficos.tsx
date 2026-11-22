"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { api } from "@/app/services/API/api"

type Graficos = {
  projetos_por_mes: { mes: string; total: number }[]
  projetos_por_status: { status: string; total: number }[]
  equipe: {
    profissionais: number
    media_projetos_por_profissional: number
    sem_projeto: number
    competencias: number
  }
  top_competencias: { id: number; nome: string; total: number }[]
  top_profissionais: { id: number; nome: string; total: number }[]
}

// "2026-06" -> Date no dia 1 (meio-dia, para não virar o mês anterior por fuso)
const dataDoMes = (mes: string) => new Date(`${mes}-01T12:00:00`)
const mesCurto = (mes: string) =>
  dataDoMes(mes).toLocaleDateString("pt-BR", { month: "short" }).replace(".", "")
const mesLongo = (mes: string) =>
  dataDoMes(mes).toLocaleDateString("pt-BR", { month: "long", year: "numeric" })

const plural = (n: number, um: string, varios: string) => `${n} ${n === 1 ? um : varios}`
const decimal = (n: number) => n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })

export default function DashboardGraficos() {
  const [dados, setDados] = useState<Graficos | null>(null)
  const [erro, setErro] = useState(false)

  useEffect(() => {
    let ativo = true
    api
      .get<Graficos>("/api/dashboard/graficos/")
      .then((d) => {
        if (ativo) setDados(d)
      })
      .catch(() => {
        if (ativo) setErro(true)
      })
    return () => {
      ativo = false
    }
  }, [])

  if (erro) {
    return (
      <p role="alert" className="text-sm text-red-300">
        Não foi possível carregar os gráficos do dashboard.
      </p>
    )
  }
  if (!dados) return <div className="h-64 rounded-2xl bg-(--surface-elevated) animate-pulse" aria-busy="true" />

  const { equipe } = dados

  return (
    <div className="flex flex-col gap-6">
      <section aria-label="Equipe" className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Indicador
          rotulo="Média de projetos por profissional"
          valor={decimal(equipe.media_projetos_por_profissional)}
        />
        <Indicador rotulo="Profissionais" valor={String(equipe.profissionais)} href="/profissionais" />
        <Indicador
          rotulo="Profissionais sem projeto"
          valor={String(equipe.sem_projeto)}
          detalhe={
            equipe.profissionais
              ? `${Math.round((equipe.sem_projeto * 100) / equipe.profissionais)}% da equipe`
              : undefined
          }
        />
        <Indicador rotulo="Competências" valor={String(equipe.competencias)} href="/competencias" />
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Cartao titulo="Projetos criados por mês" subtitulo="Últimos 6 meses">
          <Colunas
            itens={dados.projetos_por_mes.map((m) => ({
              chave: m.mes,
              rotulo: mesCurto(m.mes),
              rotuloLongo: mesLongo(m.mes),
              valor: m.total,
            }))}
            unidade={["projeto", "projetos"]}
          />
        </Cartao>

        <Cartao titulo="Projetos por status" subtitulo="Situação atual dos seus projetos">
          <Barras
            itens={dados.projetos_por_status.map((s) => ({ chave: s.status, rotulo: s.status, valor: s.total }))}
            unidade={["projeto", "projetos"]}
            vazio="Nenhum projeto cadastrado."
          />
        </Cartao>

        <Cartao titulo="Competências mais comuns" subtitulo="Quantos profissionais têm cada uma">
          <Barras
            itens={dados.top_competencias.map((c) => ({ chave: String(c.id), rotulo: c.nome, valor: c.total }))}
            unidade={["profissional", "profissionais"]}
            vazio="Nenhuma competência vinculada a profissionais."
          />
        </Cartao>

        <Cartao titulo="Profissionais em mais projetos" subtitulo="Projetos distintos de que cada um participa">
          <Barras
            itens={dados.top_profissionais.map((p) => ({
              chave: String(p.id),
              rotulo: p.nome,
              valor: p.total,
              href: `/profissionais/${p.id}`,
            }))}
            unidade={["projeto", "projetos"]}
            vazio="Nenhuma participação em projetos registrada."
          />
        </Cartao>
      </div>
    </div>
  )
}

function Indicador({
  rotulo,
  valor,
  detalhe,
  href,
}: {
  rotulo: string
  valor: string
  detalhe?: string
  href?: string
}) {
  const conteudo = (
    <>
      <span className="text-secondary text-xs">{rotulo}</span>
      <span className="text-white text-2xl font-semibold">{valor}</span>
      {detalhe && <span className="text-secondary text-xs">{detalhe}</span>}
    </>
  )
  const classe =
    "rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4 flex flex-col gap-1 min-w-0"
  return href ? (
    <Link href={href} className={`${classe} hover:border-gray-600 transition-colors`}>
      {conteudo}
    </Link>
  ) : (
    <div className={classe}>{conteudo}</div>
  )
}

function Cartao({ titulo, subtitulo, children }: { titulo: string; subtitulo: string; children: React.ReactNode }) {
  return (
    <section
      aria-label={titulo}
      className="rounded-2xl border border-gray-800/50 bg-(--surface-elevated) p-4 sm:p-5 flex flex-col gap-4 min-w-0"
    >
      <div>
        <h2 className="text-white text-sm sm:text-base font-semibold">{titulo}</h2>
        <p className="text-secondary text-xs mt-0.5">{subtitulo}</p>
      </div>
      {children}
    </section>
  )
}

type Coluna = { chave: string; rotulo: string; rotuloLongo: string; valor: number }

// Colunas verticais de uma série: ≤24px de largura, ponta arredondada, valor no topo
function Colunas({ itens, unidade }: { itens: Coluna[]; unidade: [string, string] }) {
  const [ativo, setAtivo] = useState<string | null>(null)
  const maximo = Math.max(1, ...itens.map((i) => i.valor))
  const ALTURA = 140

  return (
    <div>
      <div className="relative flex items-end gap-2 border-b border-gray-700/60" style={{ height: ALTURA + 24 }}>
        {itens.map((item) => {
          const altura = item.valor === 0 ? 0 : Math.max(4, (item.valor / maximo) * ALTURA)
          const descricao = `${item.rotuloLongo}: ${plural(item.valor, ...unidade)}`
          return (
            <div
              key={item.chave}
              tabIndex={0}
              role="img"
              aria-label={descricao}
              onMouseEnter={() => setAtivo(item.chave)}
              onMouseLeave={() => setAtivo(null)}
              onFocus={() => setAtivo(item.chave)}
              onBlur={() => setAtivo(null)}
              className="relative flex-1 h-full flex flex-col items-center justify-end outline-none focus-visible:bg-white/5 rounded-t-md"
            >
              {ativo === item.chave && (
                <span className="absolute -top-2 left-1/2 -translate-x-1/2 -translate-y-full z-10 whitespace-nowrap rounded-md border border-gray-700/60 bg-(--surface-base) px-2 py-1 text-xs text-white shadow-lg">
                  {descricao}
                </span>
              )}
              <span className="text-xs text-white mb-1">{item.valor}</span>
              <span
                className={`w-full max-w-6 rounded-t bg-primary transition-opacity ${
                  ativo && ativo !== item.chave ? "opacity-60" : ""
                }`}
                style={{ height: altura }}
              />
            </div>
          )
        })}
      </div>
      <div className="flex gap-2 mt-2">
        {itens.map((item) => (
          <span key={item.chave} className="flex-1 text-center text-xs text-secondary capitalize">
            {item.rotulo}
          </span>
        ))}
      </div>
    </div>
  )
}

type Barra = { chave: string; rotulo: string; valor: number; href?: string }

// Barras horizontais de uma série, com o valor na ponta
function Barras({ itens, unidade, vazio }: { itens: Barra[]; unidade: [string, string]; vazio: string }) {
  if (itens.length === 0 || itens.every((i) => i.valor === 0)) {
    return <p className="text-secondary text-sm">{vazio}</p>
  }
  const maximo = Math.max(1, ...itens.map((i) => i.valor))

  return (
    <ul className="flex flex-col gap-3">
      {itens.map((item) => {
        const descricao = `${item.rotulo}: ${plural(item.valor, ...unidade)}`
        return (
          <li key={item.chave} className="grid grid-cols-[minmax(0,9rem)_minmax(0,1fr)] items-center gap-3" title={descricao}>
            {item.href ? (
              <Link href={item.href} className="text-sm text-white truncate hover:text-primary transition-colors">
                {item.rotulo}
              </Link>
            ) : (
              <span className="text-sm text-white truncate">{item.rotulo}</span>
            )}
            <div className="flex items-center gap-2 min-w-0" role="img" aria-label={descricao}>
              {item.valor > 0 && (
                <span
                  className="h-2.5 rounded-r bg-primary"
                  style={{ width: `${(item.valor / maximo) * 85}%` }}
                />
              )}
              <span className="text-xs text-secondary shrink-0">{item.valor}</span>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
