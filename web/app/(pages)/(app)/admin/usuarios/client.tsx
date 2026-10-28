"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { RefreshCw, Search, Trash2, UserCheck, UserX, X } from "lucide-react"
import { useAuth } from "@/app/contexts/AuthContext"
import {
  alterarEstadoLogin,
  encerrarSessao,
  excluirLogin,
  listarUsuarios,
  mensagemDeErro,
  sessaoInvalida,
} from "@/app/services/API/usuarios"
import type { UsuarioAdmin } from "@/app/types/api/usuario"

type Filtro = "todos" | "ativos" | "desativados"
type Acao = { tipo: "desativar" | "reativar" | "excluir"; alvo: UsuarioAdmin }

const FILTROS: { valor: Filtro; label: string }[] = [
  { valor: "todos", label: "Todos" },
  { valor: "ativos", label: "Ativos" },
  { valor: "desativados", label: "Desativados" },
]

// Texto de cada confirmação: o que vai acontecer e se dá para desfazer
function textoDaAcao(acao: Acao) {
  const quem = `${acao.alvo.nome} (${acao.alvo.email})`
  switch (acao.tipo) {
    case "desativar":
      return {
        titulo: "Desativar login?",
        descricao: `${quem} não conseguirá mais entrar na plataforma e as sessões abertas serão encerradas. Você pode reativar o login depois.`,
        botao: "Desativar",
      }
    case "reativar":
      return {
        titulo: "Reativar login?",
        descricao: `${quem} voltará a poder entrar na plataforma.`,
        botao: "Reativar",
      }
    case "excluir":
      return {
        titulo: "Excluir login?",
        descricao: `${quem} perderá o acesso e o login não poderá ser reativado pela plataforma. Os projetos e documentos dele serão mantidos.`,
        botao: "Excluir",
      }
  }
}

function UsuariosAdmin() {
  const router = useRouter()
  const { usuario: logado } = useAuth()

  const [usuarios, setUsuarios] = useState<UsuarioAdmin[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [recarga, setRecarga] = useState(0)
  const [filtro, setFiltro] = useState<Filtro>("todos")
  const [busca, setBusca] = useState("")
  const [acao, setAcao] = useState<Acao | null>(null)
  const [processando, setProcessando] = useState(false)
  const [erroAcao, setErroAcao] = useState("")
  const [aviso, setAviso] = useState("")

  // Quem não é admin não tem nada a fazer aqui (a API também barra com 403)
  useEffect(() => {
    if (logado && !logado.is_admin) router.replace("/dashboard")
  }, [logado, router])

  useEffect(() => {
    let ativo = true

    listarUsuarios()
      .then((lista) => {
        if (!ativo) return
        setUsuarios(lista)
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

  // Esc fecha a confirmação (a menos que a requisição esteja em andamento)
  useEffect(() => {
    if (!acao) return
    const aoTeclar = (evento: KeyboardEvent) => {
      if (evento.key === "Escape" && !processando) setAcao(null)
    }
    window.addEventListener("keydown", aoTeclar)
    return () => window.removeEventListener("keydown", aoTeclar)
  }, [acao, processando])

  const recarregar = () => {
    setCarregando(true)
    setAviso("")
    setRecarga((n) => n + 1)
  }

  const abrirConfirmacao = (tipo: Acao["tipo"], alvo: UsuarioAdmin) => {
    setErroAcao("")
    setAviso("")
    setAcao({ tipo, alvo })
  }

  const confirmar = async () => {
    if (!acao) return
    const { tipo, alvo } = acao
    setProcessando(true)
    setErroAcao("")

    try {
      if (tipo === "excluir") {
        await excluirLogin(alvo.id)
        setUsuarios((prev) => prev.filter((u) => u.id !== alvo.id))
        setAviso(`Login de ${alvo.nome} excluído. Os projetos e documentos foram mantidos.`)
      } else {
        const atualizado = await alterarEstadoLogin(alvo.id, tipo === "reativar")
        setUsuarios((prev) => prev.map((u) => (u.id === atualizado.id ? atualizado : u)))
        setAviso(`Login de ${alvo.nome} ${tipo === "reativar" ? "reativado" : "desativado"}.`)
      }
      setAcao(null)
    } catch (e) {
      if (sessaoInvalida(e)) {
        encerrarSessao()
        return
      }
      setErroAcao(mensagemDeErro(e))
    } finally {
      setProcessando(false)
    }
  }

  const contagem = useMemo(
    () => ({
      todos: usuarios.length,
      ativos: usuarios.filter((u) => u.is_active).length,
      desativados: usuarios.filter((u) => !u.is_active).length,
    }),
    [usuarios]
  )

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase()
    return usuarios.filter((u) => {
      if (filtro === "ativos" && !u.is_active) return false
      if (filtro === "desativados" && u.is_active) return false
      if (!termo) return true
      return u.nome.toLowerCase().includes(termo) || u.email.toLowerCase().includes(termo)
    })
  }, [usuarios, filtro, busca])

  const textos = acao ? textoDaAcao(acao) : null

  return (
    <div className="w-full h-full flex flex-col flex-1 bg-background">

      {/* Cabeçalho */}
      <div className="w-full shrink-0 flex justify-between items-center gap-4 px-4 sm:px-6 lg:px-8 py-4 bg-background border-b border-gray-800/50 z-10">
        <div className="flex flex-col gap-1 min-w-0">
          <h1 className="text-white font-semibold text-lg sm:text-2xl lg:text-3xl truncate">
            Administração de logins
          </h1>
          <span className="text-secondary text-xs sm:text-sm">
            Gerencie o acesso dos POs à plataforma
          </span>
        </div>
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

      {/* Conteúdo */}
      <div className="w-full flex-1 min-h-0 overflow-y-auto flex flex-col gap-4 px-4 sm:px-6 lg:px-8 py-6">

        {/* Busca e filtros */}
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="relative w-full md:max-w-sm">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
            <input
              type="text"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar por nome ou e-mail"
              aria-label="Buscar por nome ou e-mail"
              className="w-full h-11 bg-(--surface-elevated) outline-none rounded-xl pl-10 pr-4 text-sm text-white border border-gray-700/50 focus:ring-2 focus:ring-primary transition duration-200"
            />
          </div>

          <div className="flex gap-2 flex-wrap" role="group" aria-label="Filtrar por estado">
            {FILTROS.map((f) => (
              <button
                key={f.valor}
                type="button"
                onClick={() => setFiltro(f.valor)}
                aria-pressed={filtro === f.valor}
                className={`h-10 px-4 rounded-lg text-sm font-medium border transition-colors ${
                  filtro === f.valor
                    ? "bg-primary text-white border-primary"
                    : "bg-(--surface-elevated) text-secondary border-gray-800/50 hover:text-white"
                }`}
              >
                {f.label} ({contagem[f.valor]})
              </button>
            ))}
          </div>
        </div>

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

        {/* Estados da lista */}
        {carregando && (
          <div className="text-secondary text-sm animate-pulse">Carregando logins...</div>
        )}

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

        {!carregando && !erro && visiveis.length === 0 && (
          <div className="text-secondary text-sm">Nenhum login encontrado.</div>
        )}

        {!carregando && !erro && visiveis.length > 0 && (
          <ul className="flex flex-col gap-2">
            {visiveis.map((u) => {
              const ehVoce = logado?.id === u.id
              return (
                <li
                  key={u.id}
                  className="bg-(--surface-elevated) border border-gray-800/50 rounded-xl px-4 py-3 flex flex-col gap-3 md:flex-row md:items-center md:justify-between"
                >
                  <div className="flex flex-col min-w-0">
                    <span className="text-white text-sm sm:text-base font-medium truncate">{u.nome}</span>
                    <span className="text-secondary text-xs sm:text-sm truncate">{u.email}</span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {u.is_admin && (
                      <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-primary/15 text-primary">
                        Admin
                      </span>
                    )}
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                        u.is_active ? "bg-green-500/15 text-green-400" : "bg-yellow-500/15 text-yellow-400"
                      }`}
                    >
                      {u.is_active ? "Ativo" : "Desativado"}
                    </span>

                    {ehVoce ? (
                      <span className="text-xs text-secondary px-2">Você</span>
                    ) : (
                      <>
                        {u.is_active ? (
                          <button
                            type="button"
                            onClick={() => abrirConfirmacao("desativar", u)}
                            aria-label={`Desativar login de ${u.nome}`}
                            className="h-9 px-3 rounded-lg flex items-center gap-2 text-sm text-white border border-gray-700/50 hover:bg-(--surface-base) transition-colors"
                          >
                            <UserX size={16} /> Desativar
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => abrirConfirmacao("reativar", u)}
                            aria-label={`Reativar login de ${u.nome}`}
                            className="h-9 px-3 rounded-lg flex items-center gap-2 text-sm text-white border border-gray-700/50 hover:bg-(--surface-base) transition-colors"
                          >
                            <UserCheck size={16} /> Reativar
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => abrirConfirmacao("excluir", u)}
                          aria-label={`Excluir login de ${u.nome}`}
                          className="h-9 px-3 rounded-lg flex items-center gap-2 text-sm text-red-400 border border-red-500/30 hover:bg-red-500/10 transition-colors"
                        >
                          <Trash2 size={16} /> Excluir
                        </button>
                      </>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      {/* Confirmação */}
      {acao && textos && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="titulo-confirmacao"
            className="w-full max-w-md bg-(--surface-base) border border-gray-800/50 rounded-2xl p-6 flex flex-col gap-4 shadow-2xl"
          >
            <h2 id="titulo-confirmacao" className="text-white text-lg font-semibold">
              {textos.titulo}
            </h2>
            <p className="text-secondary text-sm">{textos.descricao}</p>

            {erroAcao && (
              <p role="alert" className="text-sm text-red-300">
                {erroAcao}
              </p>
            )}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                autoFocus
                onClick={() => setAcao(null)}
                disabled={processando}
                className="h-10 px-4 rounded-lg text-sm text-white border border-gray-700/50 hover:bg-(--surface-elevated) transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={confirmar}
                disabled={processando}
                className={`h-10 px-4 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50 ${
                  acao.tipo === "excluir" ? "bg-red-600 hover:bg-red-700" : "bg-primary hover:bg-primary-dark"
                }`}
              >
                {processando ? "Aguarde..." : textos.botao}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default UsuariosAdmin