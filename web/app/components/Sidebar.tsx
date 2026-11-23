"use client"
import { useState, useEffect } from "react"
import { createPortal } from "react-dom"
import { usePathname, useRouter } from "next/navigation"
import {
  PanelLeftClose,
  PanelLeftOpen,
  Menu,
  MessageSquare,
  MoreHorizontal,
  Trash2,
} from "lucide-react"
import Link from "next/link"
import Logo from "./Logo"
import {
  PAGINAS_PRINCIPAIS,
  PAGINAS_ADMIN,
  PAGINAS_CONFIG,
} from "@/app/constants/navigation"
import { useAuth } from "@/app/contexts/AuthContext"
import { SidebarItem } from "./app/SidebarItem"
import { excluirConversa } from "@/app/services/API/chat"

type ConversaResumo = {
  id: number
  titulo: string
  atualizado_em: string
}

function formatarData(iso: string) {
  const data = new Date(iso)
  const hoje = new Date()
  const ontem = new Date(hoje)
  ontem.setDate(hoje.getDate() - 1)

  const mesmoDia = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()

  if (mesmoDia(data, hoje)) return "HOJE"
  if (mesmoDia(data, ontem)) return "ONTEM"
  return data
    .toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })
    .toUpperCase()
}

export default function Sidebar() {
  const [expandido, setExpandido] = useState(false)
  const [conversas, setConversas] = useState<ConversaResumo[]>([])
  const [menu, setMenu] = useState<{
    id: number
    top: number
    left: number
  } | null>(null)
  const [excluindoId, setExcluindoId] = useState<number | null>(null)
  const pathname = usePathname()
  const router = useRouter()
  const { usuario } = useAuth()

  const paginasPrincipais = usuario?.is_admin
    ? [...PAGINAS_PRINCIPAIS, ...PAGINAS_ADMIN]
    : PAGINAS_PRINCIPAIS

  useEffect(() => {
    if (window.innerWidth < 768) {
      setExpandido(false)
    }
  }, [pathname])

  useEffect(() => {
    fetch("http://localhost:8000/api/conversas/", { credentials: "include" })
      .then((res) => (res.ok ? res.json() : []))
      .then(setConversas)
      .catch(() => setConversas([]))
  }, [])

  // fecha o menu ao recolher a sidebar
  useEffect(() => {
    if (!expandido) setMenu(null)
  }, [expandido])

  // fecha o menu com Esc, ao redimensionar ou ao rolar a lista
  useEffect(() => {
    if (!menu) return
    const fechar = () => setMenu(null)
    const esc = (e: KeyboardEvent) => {
      if (e.key === "Escape") fechar()
    }
    window.addEventListener("keydown", esc)
    window.addEventListener("resize", fechar)
    window.addEventListener("scroll", fechar, true) // captura o scroll da lista
    return () => {
      window.removeEventListener("keydown", esc)
      window.removeEventListener("resize", fechar)
      window.removeEventListener("scroll", fechar, true)
    }
  }, [menu])

  const abrirMenu = (e: React.MouseEvent<HTMLButtonElement>, id: number) => {
    e.preventDefault() // não segue o <Link>
    e.stopPropagation()
    if (menu?.id === id) return setMenu(null)
    const r = e.currentTarget.getBoundingClientRect()
    setMenu({ id, top: r.bottom + 4, left: Math.max(8, r.right - 140) })
  }

  const excluir = async (id: number) => {
    setMenu(null)
    if (!confirm("Excluir esta conversa? Essa ação não pode ser desfeita."))
      return
    setExcluindoId(id)
    try {
      await excluirConversa(id)
      setConversas((prev) => prev.filter((c) => c.id !== id))
      // se a conversa excluída era a aberta, volta para um chat novo
      if (pathname === `/chatbot/${id}`) router.push("/chatbot")
    } catch {
      alert("Não foi possível excluir a conversa.")
    } finally {
      setExcluindoId(null)
    }
  }

  return (
    <>
      <button
        className={`
          md:hidden fixed top-5 left-5 z-40 p-2.5 rounded-lg
          text-(--foreground-muted) hover:text-primary shadow-xl transition-all duration-300
          ${expandido ? "opacity-0 -translate-x-full pointer-events-none" : "opacity-100 translate-x-0"}
        `}
        onClick={() => setExpandido(true)}
      >
        <Menu size={22} />
      </button>

      {expandido && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-40 transition-opacity"
          onClick={() => setExpandido(false)}
        />
      )}

      <aside
        className={`
          fixed md:relative top-0 left-0 z-50 h-full bg-background border-r border-gray-800/50
          flex flex-col py-4 transition-all duration-300 ease-in-out
          ${
            expandido
              ? "translate-x-0 w-65 px-3 shadow-2xl md:shadow-none"
              : "-translate-x-full w-65 md:translate-x-0 md:w-17 md:px-2 md:items-center"
          }
        `}
      >
        <div
          className={`flex w-full items-center mb-6 h-10 ${expandido ? "justify-between px-1" : "justify-center"}`}
        >
          <div
            className={`flex items-center gap-2 overflow-hidden transition-all duration-300 ${expandido ? "max-w-37.5 opacity-100" : "max-w-0 opacity-0 hidden md:flex"}`}
          >
            <div className="shrink-0">
              <Logo altura={24} largura={24} />
            </div>
            <h1 className="text-white text-sm font-semibold whitespace-nowrap tracking-wide">
              AI4PO
            </h1>
          </div>

          <button
            className="flex items-center justify-center p-2 rounded-lg text-(--foreground-muted) hover:text-white hover:bg-(--surface-elevated) transition-colors duration-200"
            onClick={() => setExpandido(!expandido)}
          >
            {expandido ? (
              <PanelLeftClose size={20} />
            ) : (
              <PanelLeftOpen size={20} className="hidden md:block" />
            )}
          </button>
        </div>

        <nav className="w-full flex flex-col gap-1">
          {paginasPrincipais.map((pagina) => (
            <SidebarItem key={pagina.rota} {...pagina} expandido={expandido} />
          ))}
        </nav>

        <div className="flex-1 overflow-hidden flex flex-col mt-6 mb-2">
          {expandido && (
            <div className="flex flex-col h-full animate-in fade-in duration-300">
              <h2 className="px-3 text-xs font-semibold text-(--foreground-muted) uppercase tracking-wider mb-2 shrink-0">
                Histórico Recente
              </h2>

              <div className="flex-1 overflow-y-auto flex flex-col gap-1 pr-1 scrollbar-thin">
                {conversas.length === 0 && (
                  <span className="px-3 text-xs text-(--foreground-muted)">
                    Nenhuma conversa ainda.
                  </span>
                )}
                {conversas.map((conversa) => {
                  const ativa = pathname === `/chatbot/${conversa.id}`
                  const menuAberto = menu?.id === conversa.id
                  return (
                    <div
                      key={conversa.id}
                      className={`relative group ${excluindoId === conversa.id ? "opacity-50 pointer-events-none" : ""}`}
                    >
                      <Link
                        href={`/chatbot/${conversa.id}`}
                        className={`flex items-center gap-3 px-3 py-2 pr-10 rounded-lg hover:bg-(--surface-elevated) transition-colors duration-200 ${ativa ? "bg-(--surface-elevated)" : ""}`}
                      >
                        <MessageSquare
                          size={16}
                          className="text-(--foreground-muted) shrink-0"
                        />
                        <div className="flex flex-col overflow-hidden">
                          <span className="text-white text-sm truncate group-hover:text-primary transition-colors">
                            {conversa.titulo || "Nova conversa"}
                          </span>
                          <span className="text-(--foreground-muted) text-[10px] uppercase font-medium mt-0.5">
                            {formatarData(conversa.atualizado_em)}
                          </span>
                        </div>
                      </Link>

                      <button
                        type="button"
                        aria-label="Opções da conversa"
                        aria-haspopup="menu"
                        aria-expanded={menuAberto}
                        onClick={(e) => abrirMenu(e, conversa.id)}
                        className={`absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-(--foreground-muted) hover:text-white hover:bg-white/10 transition ${
                          menuAberto
                            ? "opacity-100"
                            : "opacity-100 md:opacity-0 md:group-hover:opacity-100 focus:opacity-100"
                        }`}
                      >
                        <MoreHorizontal size={16} />
                      </button>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        <nav className="w-full flex flex-col gap-1">
          {PAGINAS_CONFIG.map((pagina) => (
            <SidebarItem key={pagina.rota} {...pagina} expandido={expandido} />
          ))}
        </nav>
      </aside>

      {menu &&
        createPortal(
          <>
            <div
              className="fixed inset-0 z-[60]"
              onClick={() => setMenu(null)}
            />
            <div
              role="menu"
              style={{ top: menu.top, left: menu.left, width: 140 }}
              className="fixed z-[61] rounded-lg border border-gray-800 bg-(--surface-elevated) shadow-lg py-1"
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => excluir(menu.id)}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
              >
                <Trash2 size={14} />
                Excluir
              </button>
            </div>
          </>,
          document.body,
        )}
    </>
  )
}
