"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import cytoscape from "cytoscape"
import {
  ArrowLeft,
  ArrowRight,
  Maximize2,
  Minimize2,
  Minus,
  Plus,
  Scan,
  Search,
  Shuffle,
  X,
} from "lucide-react"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL

type No = {
  id: number
  nome: string
  tipo: string
  descricao: string
  projeto: number
  comunidade: number | null
  grau: number
  x: number | null
  y: number | null
}
type Aresta = { origem: number; destino: number; tipo: string; confianca: number }
type Dados = { nos: No[]; arestas: Aresta[]; temLayout: boolean }
type Pos = { x: number; y: number }
type Modo = "tipo" | "comunidade"

const FUNDO = "#0b1220"
const PAINEL = "#0f1729"
const LARANJA = "#EF7541"
const COR_NEUTRA = "#64748b"
// Passo da grade (px) para encaixar nós ao arrastar, facilitando alinhar.
const GRADE = 20

// Paleta mais suave que a original; o laranja da marca continua sendo a primeira cor.
const PALETA = [
  "#EF7541", "#6EA8FE", "#7BD88F", "#F2C94C", "#B794F4", "#4FD1C5",
  "#F687B3", "#A3B1C6", "#FF9F68", "#5FB0E8", "#9AE6B4", "#FBD38D",
]

function getCookie(nome: string): string | undefined {
  if (typeof document === "undefined") return undefined
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(nome + "="))
    ?.split("=")[1]
}

const media = (v: number[]) => v.reduce((s, x) => s + x, 0) / v.length

const normalizar = (s: string) =>
  s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")

// Nós que ainda não têm posição salva nascem perto dos vizinhos que já têm,
// em vez de empilhar tudo em (0,0). Retorna null se nada foi salvo ainda.
function posicoesIniciais(d: Dados): Map<number, Pos> | null {
  const pos = new Map<number, Pos>()
  d.nos.forEach((n) => {
    if (n.x == null || n.y == null) return
    const x = Number(n.x)
    const y = Number(n.y)
    if (Number.isFinite(x) && Number.isFinite(y)) pos.set(n.id, { x, y })
  })
  if (pos.size === 0) return null
  const todos = [...pos.values()]
  const centro = { x: media(todos.map((p) => p.x)), y: media(todos.map((p) => p.y)) }
  d.nos.forEach((n) => {
    if (pos.has(n.id)) return
    const vizinhos: Pos[] = []
    d.arestas.forEach((a) => {
      const outro = a.origem === n.id ? a.destino : a.destino === n.id ? a.origem : null
      const p = outro != null ? pos.get(outro) : undefined
      if (p) vizinhos.push(p)
    })
    const base = vizinhos.length
      ? { x: media(vizinhos.map((p) => p.x)), y: media(vizinhos.map((p) => p.y)) }
      : centro
    pos.set(n.id, {
      x: base.x + (Math.random() - 0.5) * 90,
      y: base.y + (Math.random() - 0.5) * 90,
    })
  })
  return pos
}

// Distribui as comunidades em aglomerados compactos e determinísticos (mais
// "teia do Obsidian" que um layout aleatório). Retorna o mapa id -> posição.
function layoutPorComunidade(d: Dados): Map<number, Pos> {
  const grupos = new Map<string, No[]>()
  for (const no of d.nos) {
    const chave = no.comunidade != null ? `c:${no.comunidade}` : `t:${no.tipo || "outros"}`
    const grupo = grupos.get(chave) ?? []
    grupo.push(no)
    grupos.set(chave, grupo)
  }
  const ordenados = [...grupos.entries()].sort((a, b) => b[1].length - a[1].length)
  const colunas = Math.max(1, Math.ceil(Math.sqrt(ordenados.length * 1.35)))
  const espacamentoX = 520
  const espacamentoY = 430
  const largura = Math.max(0, (colunas - 1) * espacamentoX)
  const linhas = Math.ceil(ordenados.length / colunas)
  const altura = Math.max(0, (linhas - 1) * espacamentoY)
  const posicoes = new Map<number, Pos>()
  ordenados.forEach(([, nos], indice) => {
    const centroX = (indice % colunas) * espacamentoX - largura / 2
    const centroY = Math.floor(indice / colunas) * espacamentoY - altura / 2
    const raio = Math.max(42, Math.min(145, 25 * Math.sqrt(nos.length)))
    const lista = [...nos].sort((a, b) => (b.grau ?? 0) - (a.grau ?? 0))
    lista.forEach((no, i) => {
      if (lista.length === 1) {
        posicoes.set(no.id, { x: centroX, y: centroY })
        return
      }
      const angulo = (2 * Math.PI * i) / lista.length - Math.PI / 2
      const fator = (no.grau ?? 0) > 4 ? 0.68 : 1
      posicoes.set(no.id, {
        x: centroX + Math.cos(angulo) * raio * fator,
        y: centroY + Math.sin(angulo) * raio * fator,
      })
    })
  })
  return posicoes
}

type Catalogo = {
  tiposOrd: [string, number][]
  comsOrd: [number, number][]
  corTipo: Record<string, string>
  corCom: Record<number, string>
  comunidadesReais: number
}

function corDoNo(modo: Modo, cat: Catalogo, tipo: string, com: number) {
  return modo === "tipo"
    ? cat.corTipo[tipo] ?? COR_NEUTRA
    : cat.corCom[com] ?? COR_NEUTRA
}

// ---------------------------------------------------------------------------
// Estilo do grafo. Cores vêm de data(cor), então trocar "colorir por" é só
// atualizar o dado; as classes controlam hover, foco, busca e filtro.
// ---------------------------------------------------------------------------
const ESTILO: any[] = [
  {
    selector: "node",
    style: {
      label: "data(label)",
      "font-family": "Inter, ui-sans-serif, system-ui, sans-serif",
      "font-size": 11,
      color: "#d7deea",
      "text-valign": "bottom",
      "text-margin-y": 5,
      "text-wrap": "ellipsis",
      "text-max-width": 120,
      "text-opacity": 0, // rótulos aparecem por zoom/grau (classe .rotulo)
      "text-background-color": FUNDO,
      "text-background-opacity": 0.75,
      "text-background-padding": 2,
      "text-background-shape": "roundrectangle",
      "background-color": "data(cor)",
      width: "data(tam)",
      height: "data(tam)",
      "border-width": 1.5,
      "border-color": "data(cor)",
      "border-opacity": 0.4,
      "underlay-color": "data(cor)", // o halo
      "underlay-opacity": 0.10,
      "underlay-padding": 7,
      "underlay-shape": "ellipse",
      "overlay-opacity": 0,
      "transition-property": "opacity, underlay-opacity, border-opacity",
      "transition-duration": 150,
    },
  },
  { selector: "node.rotulo", style: { "text-opacity": 1 } },
  { selector: "node.vizinho", style: { "text-opacity": 1 } },
  {
    selector: "node.foco",
    style: {
      "underlay-opacity": 0.38,
      "border-opacity": 1,
      "border-width": 2.5,
      color: "#ffffff",
      "text-opacity": 1,
    },
  },
  { selector: "node.fixo", style: { "border-width": 3, "border-color": "#ffffff", "border-opacity": 0.85 } },
  {
    selector: "node.achado",
    style: {
      "border-color": "#ffffff",
      "border-width": 3,
      "border-opacity": 1,
      "text-opacity": 1,
    },
  },
  { selector: "node.apagado", style: { opacity: 0.18 } },
  { selector: "node.esmaecido", style: { opacity: 0.1, "text-opacity": 0 } },
  { selector: ".oculto", style: { display: "none" } },
  { selector: ".foraLocal", style: { display: "none" } },
  {
    selector: "edge",
    style: {
      width: "mapData(confianca, 0, 1, 0.8, 2.2)",
      "line-color": "#334155",
      "line-opacity": 0.16,
      "target-arrow-shape": "triangle",
      "target-arrow-color": "#334155",
      "arrow-scale": 0.6,
      "curve-style": "bezier",
      "overlay-opacity": 0,
    },
  },
  {
    selector: "edge.destaque",
    style: {
      "line-color": LARANJA,
      "target-arrow-color": LARANJA,
      "line-opacity": 0.9,
      label: "data(tipo)",
      "font-size": 8,
      color: "#f3c2a8",
      "text-rotation": "autorotate",
      "text-background-color": FUNDO,
      "text-background-opacity": 0.85,
      "text-background-padding": 2,
    },
  },
  { selector: "edge.esmaecido", style: { opacity: 0.05 } },
  { selector: "edge.escondeCruzada", style: { display: "none" } },
]

interface Props {
  // Sem projetoId = grafo GLOBAL (todos os projetos). Com projetoId = só aquele.
  projetoId?: number
  altura?: number
}

export default function GrafoViewer({ projetoId, altura = 520 }: Props) {
  const wrapperRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<cytoscape.Core | null>(null)
  const hoverRef = useRef<string | null>(null)
  const selRef = useRef<string | null>(null)
  const limiarRef = useRef(-1)
  const salvarRef = useRef<() => void>(() => {})

  const [dados, setDados] = useState<Dados | null>(null)
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [salvo, setSalvo] = useState<"idle" | "salvando" | "salvo">("idle")

  const [modo, setModo] = useState<Modo>("tipo")
  const [ocultos, setOcultos] = useState<Set<string>>(new Set())
  const [busca, setBusca] = useState("")
  const [selId, setSelId] = useState<string | null>(null)
  const [tip, setTip] = useState<{ id: string; x: number; y: number } | null>(null)
  const [tela, setTela] = useState(false)
  const [cyVersao, setCyVersao] = useState(0)
  const [focoLocal, setFocoLocal] = useState(false)
  const [fixos, setFixos] = useState<Set<string>>(new Set())
  const [mostrarCruzadas, setMostrarCruzadas] = useState(false)

  // ---- carga ---------------------------------------------------------------
  useEffect(() => {
    let vivo = true
    setCarregando(true)
    setErro("")
    setDados(null)
    setSelId(null)
    selRef.current = null
    setOcultos(new Set())
    const url =
      projetoId != null
        ? `${BASE_URL}/api/grafo/dados/?projeto=${projetoId}`
        : `${BASE_URL}/api/grafo/dados/`
    fetch(url, { credentials: "include" })
      .then((r) => {
        if (!r.ok) throw new Error(String(r.status))
        return r.json()
      })
      .then((d: Dados) => {
        if (!vivo) return
        // Se o grafo tem comunidades de verdade, começa colorindo por elas;
        // senão por tipo (evita o "tudo laranja" quando comunidade é null).
        const reais = new Set(d.nos.filter((n) => n.comunidade != null).map((n) => n.comunidade))
        setModo(reais.size >= 2 ? "comunidade" : "tipo")
        setDados(d)
      })
      .catch(() => vivo && setErro("Não foi possível carregar o grafo."))
      .finally(() => vivo && setCarregando(false))
    return () => {
      vivo = false
    }
  }, [projetoId])

  // ---- dados derivados -----------------------------------------------------
  const porId = useMemo(() => {
    const m = new Map<string, No>()
    dados?.nos.forEach((n) => m.set(String(n.id), n))
    return m
  }, [dados])

  const catalogo = useMemo<Catalogo>(() => {
    const tipos = new Map<string, number>()
    const coms = new Map<number, number>()
    dados?.nos.forEach((n) => {
      tipos.set(n.tipo, (tipos.get(n.tipo) ?? 0) + 1)
      const c = n.comunidade ?? -1
      coms.set(c, (coms.get(c) ?? 0) + 1)
    })
    const tiposOrd = [...tipos.entries()].sort((a, b) => b[1] - a[1])
    const comsOrd = [...coms.entries()].sort((a, b) => a[0] - b[0])
    const corTipo: Record<string, string> = {}
    ;[...tipos.keys()].sort().forEach((t, i) => (corTipo[t] = PALETA[i % PALETA.length]))
    const corCom: Record<number, string> = {}
    let i = 0
    comsOrd.forEach(([c]) => {
      corCom[c] = c === -1 ? COR_NEUTRA : PALETA[i++ % PALETA.length]
    })
    return {
      tiposOrd,
      comsOrd,
      corTipo,
      corCom,
      comunidadesReais: comsOrd.filter(([c]) => c !== -1).length,
    }
  }, [dados])

  // refs com o valor mais recente para os handlers do Cytoscape
  const modoRef = useRef(modo)
  const catalogoRef = useRef(catalogo)
  modoRef.current = modo
  catalogoRef.current = catalogo

  const conexoes = useMemo(() => {
    if (!selId || !dados) return []
    const id = Number(selId)
    return dados.arestas
      .flatMap((a) =>
        a.origem === id
          ? [{ saindo: true, outro: a.destino, tipo: a.tipo, conf: a.confianca }]
          : a.destino === id
            ? [{ saindo: false, outro: a.origem, tipo: a.tipo, conf: a.confianca }]
            : []
      )
      .sort((a, b) => b.conf - a.conf)
  }, [selId, dados])

  // ---- foco (hover / seleção) e rótulos por zoom -----------------------------
  const aplicarFoco = useCallback(() => {
    const cy = cyRef.current
    if (!cy) return
    const alvoId = hoverRef.current ?? selRef.current
    cy.batch(() => {
      cy.elements().removeClass("foco esmaecido vizinho destaque")
      if (!alvoId) return
      const alvo = cy.getElementById(alvoId)
      if (alvo.empty()) return
      const viz = alvo.closedNeighborhood()
      cy.elements().not(viz).addClass("esmaecido")
      viz.addClass("vizinho")
      alvo.addClass("foco")
      alvo.connectedEdges().addClass("destaque")
    })
  }, [])

  // Como no Obsidian: afastado só os nós mais conectados têm nome; perto, todos.
  const atualizarRotulos = useCallback((cy: cytoscape.Core) => {
    const z = cy.zoom()
    const limiar = z >= 1.5 ? 0 : z >= 1 ? 2 : z >= 0.65 ? 4 : 7
    if (limiar === limiarRef.current) return
    limiarRef.current = limiar
    cy.batch(() => {
      cy.nodes().forEach((n) => {
        n.toggleClass("rotulo", (n.data("grau") ?? 0) >= limiar)
      })
    })
  }, [])

  const selecionar = useCallback(
    (id: string | null) => {
      selRef.current = id
      setSelId(id)
      if (id == null) setFocoLocal(false)
      aplicarFoco()
    },
    [aplicarFoco]
  )

  const centralizar = useCallback((id: string) => {
    const cy = cyRef.current
    if (!cy) return
    const no = cy.getElementById(id)
    if (no.empty()) return
    cy.animate(
      { center: { eles: no }, zoom: Math.max(cy.zoom(), 1.1) },
      { duration: 300 }
    )
  }, [])

  // ---- persistência de posições (mesma API de antes) -------------------------
  const salvarPosicoes = useCallback(
    async (cy: cytoscape.Core) => {
      const posicoes: Record<string, Pos> = {}
      cy.nodes().forEach((n) => {
        const p = n.position()
        posicoes[n.id()] = { x: Math.round(p.x), y: Math.round(p.y) }
      })
      setSalvo("salvando")
      try {
        await fetch(`${BASE_URL}/api/grafo/posicoes/`, {
          method: "PUT",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken") || "",
          },
          body: JSON.stringify({ projeto: projetoId ?? null, posicoes }),
        })
        setSalvo("salvo")
        setTimeout(() => setSalvo("idle"), 1500)
      } catch {
        setSalvo("idle")
      }
    },
    [projetoId]
  )
  salvarRef.current = () => cyRef.current && salvarPosicoes(cyRef.current)

  // ---- monta o Cytoscape quando os dados chegam ----------------------------
  useEffect(() => {
    const el = containerRef.current
    if (!dados || !el) return

    // Preserva posições salvas; sem nada salvo, abre com as comunidades agrupadas
    // (determinístico e mais legível que um layout aleatório).
    const pos = posicoesIniciais(dados) ?? layoutPorComunidade(dados)
    const ids = new Set(dados.nos.map((n) => n.id))
    const comPorId = new Map(dados.nos.map((n) => [n.id, n.comunidade ?? -1]))
    const layout: any = { name: "preset" }

    const cy = cytoscape({
      container: el,
      elements: {
        nodes: dados.nos.map((n) => ({
          data: {
            id: String(n.id),
            label: n.nome,
            tipo: n.tipo,
            comunidade: n.comunidade ?? -1,
            grau: n.grau ?? 0,
            tam: 10 + Math.min(26, Math.sqrt(n.grau ?? 0) * 6),
            cor: corDoNo(modoRef.current, catalogoRef.current, n.tipo, n.comunidade ?? -1),
          },
          position: pos?.get(n.id),
        })),
        edges: dados.arestas
          .filter((a) => ids.has(a.origem) && ids.has(a.destino))
          .map((a, i) => ({
            data: {
              id: `e${i}`,
              source: String(a.origem),
              target: String(a.destino),
              tipo: a.tipo,
              confianca: a.confianca,
              comOrigem: comPorId.get(a.origem) ?? -1,
              comDestino: comPorId.get(a.destino) ?? -1,
            },
          })),
      },
      style: ESTILO,
      layout,
      minZoom: 0.02,
      maxZoom: 3,
      wheelSensitivity: 0.25,
      autounselectify: true,
    })
    cyRef.current = cy
    limiarRef.current = -1

    // Se algum nó ficou sem posição válida (NaN/ausente), refaz com cose do zero:
    // coordenadas inválidas deixam o canvas vazio sem erro no console.
    const posInvalida = dados.nos.some((n) => {
      const p = pos.get(n.id)
      return !p || !Number.isFinite(p.x) || !Number.isFinite(p.y)
    })
    if (posInvalida) cy.layout({ name: "cose", animate: false, padding: 48 } as any).run()

    // Enquadra tudo e continua reenquadrando (primeiro frame e qualquer mudança
    // de tamanho do container) até o usuário mexer no zoom/pan/nós.
    let interagiu = false
    const enquadrar = () => {
      if (el.clientHeight > 0) cy.fit(undefined, 48)
    }
    cy.on("userzoom userpan dragfree", () => {
      interagiu = true
    })
    enquadrar()
    const raf = requestAnimationFrame(() => {
      if (!interagiu) enquadrar()
    })
    atualizarRotulos(cy)

    const ro = new ResizeObserver(() => {
      cy.resize()
      if (!interagiu) enquadrar()
    })
    ro.observe(el)

    // Só em desenvolvimento: permite inspecionar no console (window.__cy).
    if (process.env.NODE_ENV !== "production") (window as any).__cy = cy

    cy.on("mouseover", "node", (e) => {
      hoverRef.current = e.target.id()
      el.style.cursor = "pointer"
      aplicarFoco()
      const p = e.renderedPosition
      const w = cy.width()
      const h = cy.height()
      setTip({
        id: e.target.id(),
        x: Math.min(p.x + 14, w - 270),
        y: p.y + 14 > h - 110 ? p.y - 100 : p.y + 14,
      })
    })
    cy.on("mouseout", "node", () => {
      hoverRef.current = null
      el.style.cursor = "default"
      aplicarFoco()
      setTip(null)
    })
    cy.on("tap", "node", (e) => selecionar(e.target.id()))
    cy.on("tap", (e) => {
      if (e.target === cy) selecionar(null)
    })
    // Duplo-clique: seleciona e entra no modo "grafo local" (atalho pro Isolar).
    cy.on("dbtap", "node", (e) => {
      selecionar(e.target.id())
      setFocoLocal(true)
    })
    cy.on("grab zoom", () => setTip(null))
    cy.on("zoom", () => atualizarRotulos(cy))

    // Ao soltar um nó: encaixa na grade (facilita alinhar) e salva (debounce).
    let timer: ReturnType<typeof setTimeout>
    cy.on("dragfree", "node", (e) => {
      const p = e.target.position()
      e.target.position({
        x: Math.round(p.x / GRADE) * GRADE,
        y: Math.round(p.y / GRADE) * GRADE,
      })
      clearTimeout(timer)
      timer = setTimeout(() => salvarRef.current(), 600)
    })

    setCyVersao((v) => v + 1)

    return () => {
      clearTimeout(timer)
      cancelAnimationFrame(raf)
      ro.disconnect()
      hoverRef.current = null
      cy.destroy()
      cyRef.current = null
    }
  }, [dados, aplicarFoco, atualizarRotulos, selecionar])

  // ---- reações a estado: cor, filtro, busca ----------------------------------
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.batch(() => {
      cy.nodes().forEach((n) => {
        n.data("cor", corDoNo(modo, catalogo, n.data("tipo"), n.data("comunidade")))
      })
    })
  }, [modo, catalogo, cyVersao])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.batch(() => {
      cy.nodes().forEach((n) => {
        n.toggleClass(
          "oculto",
          ocultos.has(`t:${n.data("tipo")}`) || ocultos.has(`c:${n.data("comunidade")}`)
        )
      })
    })
  }, [ocultos, cyVersao])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    const q = normalizar(busca.trim())
    cy.batch(() => {
      cy.nodes().removeClass("achado apagado")
      if (!q) return
      cy.nodes().forEach((n) => {
        n.addClass(normalizar(n.data("label")).includes(q) ? "achado" : "apagado")
      })
    })
  }, [busca, cyVersao])

  // Modo "grafo local" (estilo Obsidian): mostra só o nó selecionado e suas
  // vizinhas diretas, escondendo o resto.
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.batch(() => {
      if (focoLocal && selId) {
        const alvo = cy.getElementById(selId)
        if (alvo.empty()) {
          cy.elements().removeClass("foraLocal")
          return
        }
        const viz = alvo.closedNeighborhood()
        cy.elements().removeClass("foraLocal")
        cy.elements().not(viz).addClass("foraLocal")
      } else {
        cy.elements().removeClass("foraLocal")
      }
    })
  }, [focoLocal, selId, cyVersao])

  // Marca visualmente os nós fixados (borda branca), ligando/desligando a classe.
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.batch(() => {
      cy.nodes().forEach((n) => {
        n.toggleClass("fixo", fixos.has(n.id()))
      })
    })
  }, [fixos, cyVersao])

  // Oculta as arestas que ligam comunidades diferentes (menos emaranhado no global).
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.batch(() => {
      cy.edges().forEach((e) => {
        const cruzada = e.data("comOrigem") !== e.data("comDestino")
        e.toggleClass("escondeCruzada", cruzada && !mostrarCruzadas)
      })
    })
  }, [mostrarCruzadas, cyVersao])

  // tela cheia + Esc para fechar o painel
  useEffect(() => {
    const onFs = () => setTela(document.fullscreenElement === wrapperRef.current)
    document.addEventListener("fullscreenchange", onFs)
    return () => document.removeEventListener("fullscreenchange", onFs)
  }, [])

  useEffect(() => {
    if (!selId) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !document.fullscreenElement) selecionar(null)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [selId, selecionar])

  // ---- ações da UI -----------------------------------------------------------
  function zoomPor(fator: number) {
    const cy = cyRef.current
    if (!cy) return
    cy.animate(
      {
        zoom: {
          level: cy.zoom() * fator,
          renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
        },
      },
      { duration: 150 }
    )
  }

  function ajustar() {
    const cy = cyRef.current
    if (!cy) return
    const visiveis = cy.nodes(":visible")
    cy.animate(
      { fit: { eles: visiveis.nonempty() ? visiveis : cy.elements(), padding: 48 } },
      { duration: 250 }
    )
  }

  function reorganizar() {
    const cy = cyRef.current
    if (!cy || !dados) return
    if (!window.confirm("Reorganizar o grafo por comunidades? As posições salvas serão substituídas.")) return
    const novasPosicoes = layoutPorComunidade(dados)
    cy.nodes().forEach((no) => {
      if (fixos.has(no.id())) return // respeita os nós que o usuário fixou
      const destino = novasPosicoes.get(Number(no.id()))
      if (destino) no.animate({ position: destino }, { duration: 520 })
    })
    window.setTimeout(() => {
      cy.animate({ fit: { eles: cy.elements(), padding: 72 } }, { duration: 300 })
      salvarPosicoes(cy)
    }, 560)
  }

  function alternarTela() {
    if (document.fullscreenElement) document.exitFullscreen()
    else wrapperRef.current?.requestFullscreen()
  }

  function irParaBusca() {
    const cy = cyRef.current
    if (!cy) return
    const achados = cy.nodes(".achado").not(".oculto")
    if (achados.nonempty()) cy.animate({ fit: { eles: achados, padding: 120 } }, { duration: 350 })
  }

  function alternarFiltro(chave: string) {
    setOcultos((atual) => {
      const novo = new Set(atual)
      if (novo.has(chave)) novo.delete(chave)
      else novo.add(chave)
      return novo
    })
  }

  function trocarModo(m: Modo) {
    if (m === modo) return
    setModo(m)
    setOcultos(new Set()) // a legenda é o filtro: cada modo começa com tudo visível
  }

  // ---- render ----------------------------------------------------------------
  const temNos = !!dados && dados.nos.length > 0
  const noSel = selId ? porId.get(selId) : undefined
  const noTip = tip && tip.id !== selId ? porId.get(tip.id) : undefined
  const corNo = (n: No) => corDoNo(modo, catalogo, n.tipo, n.comunidade ?? -1)

  const itensLegenda =
    modo === "tipo"
      ? catalogo.tiposOrd.map(([t, qtd]) => ({
          chave: `t:${t}`,
          rotulo: t,
          qtd,
          cor: catalogo.corTipo[t],
        }))
      : catalogo.comsOrd.map(([c, qtd]) => ({
          chave: `c:${c}`,
          rotulo: c === -1 ? "Sem comunidade" : `C${c}`,
          qtd,
          cor: catalogo.corCom[c],
        }))

  const botaoControle =
    "grid size-8 place-items-center rounded-md border border-white/10 text-gray-300 transition-colors hover:border-[#EF7541]/60 hover:text-white focus-visible:outline-2 focus-visible:outline-[#EF7541]"

  return (
    <div className="flex flex-col gap-3">
      {temNos && (
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-gray-500" />
            <input
              type="search"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") irParaBusca()
                if (e.key === "Escape") setBusca("")
              }}
              placeholder="Buscar entidade"
              aria-label="Buscar entidade no grafo"
              className="w-56 rounded-lg border border-white/10 py-1.5 pl-8 pr-3 text-sm text-gray-200 placeholder:text-gray-500 focus:border-[#EF7541]/60 focus:outline-none"
              style={{ backgroundColor: PAINEL }}
            />
          </div>

          <div
            role="group"
            aria-label="Colorir por"
            className="flex items-center rounded-lg border border-white/10 p-0.5 text-sm"
            style={{ backgroundColor: PAINEL }}
          >
            <span className="px-2 text-xs text-gray-500">Colorir por</span>
            {(["tipo", "comunidade"] as Modo[]).map((m) => (
              <button
                key={m}
                type="button"
                aria-pressed={modo === m}
                onClick={() => trocarModo(m)}
                disabled={m === "comunidade" && catalogo.comunidadesReais === 0}
                className={`rounded-md px-2.5 py-1 transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                  modo === m
                    ? "bg-[#EF7541]/15 text-[#EF7541]"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {m === "tipo" ? "Tipo" : "Comunidade"}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() => setMostrarCruzadas((v) => !v)}
            aria-pressed={mostrarCruzadas}
            title="Mostrar ou ocultar as arestas que ligam comunidades diferentes"
            className={`rounded-lg border border-white/10 px-2.5 py-1.5 text-xs transition-colors ${
              mostrarCruzadas
                ? "bg-[#EF7541]/15 text-[#EF7541]"
                : "text-gray-400 hover:text-gray-200"
            }`}
            style={{ backgroundColor: PAINEL }}
          >
            Conexões entre grupos: {mostrarCruzadas ? "visíveis" : "ocultas"}
          </button>

          <span className="ml-auto text-xs text-gray-500" aria-live="polite">
            {salvo === "salvando" && <span className="text-amber-400">Salvando…</span>}
            {salvo === "salvo" && <span className="text-green-400">Posições salvas ✓</span>}
            {salvo === "idle" &&
              `${dados!.nos.length} entidades, ${dados!.arestas.length} relações`}
          </span>
        </div>
      )}

      {temNos && (
        <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Legenda e filtros">
          {itensLegenda.map((it) => {
            const oculto = ocultos.has(it.chave)
            return (
              <button
                key={it.chave}
                type="button"
                aria-pressed={!oculto}
                onClick={() => alternarFiltro(it.chave)}
                title={oculto ? "Mostrar no grafo" : "Ocultar do grafo"}
                className={`flex items-center gap-1.5 rounded-full border border-white/10 px-2.5 py-1 text-xs transition-opacity hover:border-white/25 ${
                  oculto ? "text-gray-500 line-through opacity-50" : "text-gray-200"
                }`}
                style={{ backgroundColor: PAINEL }}
              >
                <span
                  className="size-2 rounded-full"
                  style={{ backgroundColor: it.cor, boxShadow: `0 0 6px ${it.cor}` }}
                />
                {it.rotulo}
                <span className="text-gray-500">{it.qtd}</span>
              </button>
            )
          })}
          {ocultos.size > 0 && (
            <button
              type="button"
              onClick={() => setOcultos(new Set())}
              className="px-2 text-xs text-[#EF7541] hover:underline"
            >
              Mostrar tudo
            </button>
          )}
        </div>
      )}

      <div
        ref={wrapperRef}
        className="relative w-full overflow-hidden rounded-xl border border-gray-800"
        style={{
          height: tela ? "100vh" : `${altura}px`,
          backgroundColor: FUNDO,
          backgroundImage:
            "radial-gradient(circle at 50% 40%, rgba(239,117,65,0.075), transparent 58%), radial-gradient(rgba(148,163,184,0.10) 0.8px, transparent 0.8px)",
          backgroundSize: "auto, 22px 22px",
        }}
      >
        {/* Inline de propósito: o Cytoscape injeta um <style> sem @layer com
            "position: relative" no container, que vence as classes do Tailwind v4
            (que ficam em @layer). Com position relative e sem altura, o canvas
            colapsava para 0px e o grafo não aparecia. */}
        <div
          ref={containerRef}
          style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
        />

        {/* controles de zoom */}
        {temNos && (
          <div
            className="absolute bottom-3 left-3 flex flex-col gap-1.5 rounded-lg border border-white/10 p-1.5 backdrop-blur"
            style={{ backgroundColor: `${PAINEL}e6` }}
          >
            <button type="button" className={botaoControle} onClick={() => zoomPor(1.3)} aria-label="Aproximar" title="Aproximar">
              <Plus className="size-4" />
            </button>
            <button type="button" className={botaoControle} onClick={() => zoomPor(1 / 1.3)} aria-label="Afastar" title="Afastar">
              <Minus className="size-4" />
            </button>
            <button type="button" className={botaoControle} onClick={ajustar} aria-label="Enquadrar tudo" title="Enquadrar tudo">
              <Scan className="size-4" />
            </button>
            <button type="button" className={botaoControle} onClick={reorganizar} aria-label="Reorganizar automaticamente" title="Reorganizar automaticamente">
              <Shuffle className="size-4" />
            </button>
            <button type="button" className={botaoControle} onClick={alternarTela} aria-label={tela ? "Sair da tela cheia" : "Tela cheia"} title={tela ? "Sair da tela cheia" : "Tela cheia"}>
              {tela ? <Minimize2 className="size-4" /> : <Maximize2 className="size-4" />}
            </button>
          </div>
        )}

        {/* tooltip no hover */}
        {noTip && tip && (
          <div
            className="pointer-events-none absolute z-10 w-64 rounded-lg border border-white/10 p-3 shadow-xl shadow-black/40"
            style={{ left: tip.x, top: tip.y, backgroundColor: `${PAINEL}f2` }}
          >
            <div className="flex items-center gap-2">
              <span
                className="size-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: corNo(noTip), boxShadow: `0 0 8px ${corNo(noTip)}` }}
              />
              <p className="truncate text-sm font-medium text-white">{noTip.nome}</p>
            </div>
            <p className="mt-0.5 text-xs text-gray-400">{noTip.tipo}</p>
            {noTip.descricao && (
              <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-gray-300">
                {noTip.descricao}
              </p>
            )}
          </div>
        )}

        {/* painel lateral ao clicar num nó */}
        {noSel && (
          <aside
            className="absolute bottom-3 right-3 top-3 z-20 flex w-80 max-w-[85%] flex-col rounded-lg border border-white/10 shadow-2xl shadow-black/50 backdrop-blur"
            style={{ backgroundColor: `${PAINEL}f5` }}
            aria-label={`Detalhes de ${noSel.nome}`}
          >
            <div className="flex items-start gap-3 border-b border-white/10 p-4">
              <span
                className="mt-1.5 size-3 shrink-0 rounded-full"
                style={{ backgroundColor: corNo(noSel), boxShadow: `0 0 10px ${corNo(noSel)}` }}
              />
              <div className="min-w-0 flex-1">
                <h3 className="break-words text-base font-semibold leading-snug text-white">
                  {noSel.nome}
                </h3>
                <p className="mt-1 text-xs text-gray-400">
                  {noSel.tipo}
                  {noSel.comunidade != null ? `, comunidade C${noSel.comunidade}` : ", sem comunidade"}
                </p>
              </div>
              <button
                type="button"
                onClick={() =>
                  setFixos((atual) => {
                    const novo = new Set(atual)
                    if (selId && novo.has(selId)) novo.delete(selId)
                    else if (selId) novo.add(selId)
                    return novo
                  })
                }
                aria-pressed={selId ? fixos.has(selId) : false}
                title="Fixar a posição (não se move ao reorganizar)"
                className={`shrink-0 rounded-md px-2 py-1 text-xs transition-colors ${
                  selId && fixos.has(selId)
                    ? "bg-[#EF7541]/20 text-[#EF7541]"
                    : "text-gray-400 hover:bg-white/5 hover:text-white"
                }`}
              >
                {selId && fixos.has(selId) ? "Fixado" : "Fixar"}
              </button>
              <button
                type="button"
                onClick={() => setFocoLocal((v) => !v)}
                aria-pressed={focoLocal}
                title="Mostrar só esta entidade e suas vizinhas"
                className={`shrink-0 rounded-md px-2 py-1 text-xs transition-colors ${
                  focoLocal
                    ? "bg-[#EF7541]/20 text-[#EF7541]"
                    : "text-gray-400 hover:bg-white/5 hover:text-white"
                }`}
              >
                {focoLocal ? "Local ✓" : "Isolar"}
              </button>
              <button
                type="button"
                onClick={() => selecionar(null)}
                aria-label="Fechar painel"
                className="rounded-md p-1 text-gray-400 hover:bg-white/5 hover:text-white focus-visible:outline-2 focus-visible:outline-[#EF7541]"
              >
                <X className="size-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 [scrollbar-color:#334155_transparent] [scrollbar-width:thin]">
              <p className="text-sm leading-relaxed text-gray-300">
                {noSel.descricao || "Esta entidade não tem descrição."}
              </p>

              <h4 className="mb-2 mt-5 text-sm font-medium text-gray-200">
                Conexões <span className="text-gray-500">({conexoes.length})</span>
              </h4>
              {conexoes.length === 0 ? (
                <p className="text-xs text-gray-500">Nenhuma relação acima do corte de confiança.</p>
              ) : (
                <ul className="flex flex-col gap-1">
                  {conexoes.map((c, i) => {
                    const outro = porId.get(String(c.outro))
                    if (!outro) return null
                    return (
                      <li key={`${c.outro}-${i}`}>
                        <button
                          type="button"
                          onClick={() => {
                            selecionar(String(c.outro))
                            centralizar(String(c.outro))
                          }}
                          className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-white/5 focus-visible:outline-2 focus-visible:outline-[#EF7541]"
                        >
                          {c.saindo ? (
                            <ArrowRight className="size-3.5 shrink-0 text-[#EF7541]" />
                          ) : (
                            <ArrowLeft className="size-3.5 shrink-0 text-[#6EA8FE]" />
                          )}
                          <span className="min-w-0 flex-1">
                            <span className="block truncate text-gray-200">{outro.nome}</span>
                            <span className="block truncate text-xs text-gray-500">{c.tipo}</span>
                          </span>
                          <span className="shrink-0 text-xs text-gray-500">
                            {Math.round(c.conf * 100)}%
                          </span>
                        </button>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          </aside>
        )}

        {/* estados */}
        {(carregando || erro || (dados && dados.nos.length === 0)) && (
          <div className="pointer-events-none absolute inset-0 grid place-items-center px-6 text-center">
            {carregando && <p className="text-sm text-gray-400">Carregando grafo…</p>}
            {erro && <p className="text-sm text-red-400">{erro}</p>}
            {!carregando && !erro && dados && dados.nos.length === 0 && (
              <p className="max-w-sm text-sm text-gray-400">
                Ainda não há grafo para mostrar. Envie documentos e aguarde a criação do GraphRAG.
              </p>
            )}
          </div>
        )}
      </div>

      {temNos && (
        <p className="text-xs text-gray-500">
          Arraste os nós para organizar, a posição fica salva. Clique em um nó para ver os detalhes.
        </p>
      )}
    </div>
  )
}
