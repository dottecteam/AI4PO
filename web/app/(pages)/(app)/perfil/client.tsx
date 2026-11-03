"use client"

import { useState } from "react"
import { LogOut } from "lucide-react"
import { useAuth } from "@/app/contexts/AuthContext"
import { mensagemDeErro, sair } from "@/app/services/API/usuarios"

// "Maria Souza Lima" -> "ML"; "Maria" -> "M"
function iniciais(nome: string) {
  const partes = nome.trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return "?"
  const primeira = partes[0][0]
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : ""
  return (primeira + ultima).toUpperCase()
}

function Perfil() {
  const { usuario } = useAuth()
  const [saindo, setSaindo] = useState(false)
  const [erro, setErro] = useState("")

  const aoSair = async () => {
    setSaindo(true)
    setErro("")
    try {
      // Em caso de sucesso a função já leva o navegador para o login
      await sair()
    } catch (e) {
      setErro(mensagemDeErro(e))
      setSaindo(false)
    }
  }

  return (
    <div className="w-full h-full flex flex-col flex-1 bg-background">

      {/* Cabeçalho */}
      <div className="w-full shrink-0 flex flex-col gap-1 px-4 sm:px-6 lg:px-8 py-4 bg-background border-b border-gray-800/50 z-10">
        <h1 className="text-white font-semibold text-lg sm:text-2xl lg:text-3xl">Meu perfil</h1>
        <span className="text-secondary text-xs sm:text-sm">Seus dados na plataforma</span>
      </div>

      {/* Conteúdo */}
      <div className="w-full flex-1 min-h-0 overflow-y-auto flex flex-col gap-6 px-4 sm:px-6 lg:px-8 py-6">

        {!usuario ? (
          <div role="alert" className="flex flex-col items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300 max-w-xl">
            <span>Não foi possível carregar seus dados.</span>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="h-9 px-4 rounded-lg bg-(--surface-elevated) text-white border border-gray-800/50 hover:bg-(--surface-base) transition-colors"
            >
              Tentar de novo
            </button>
          </div>
        ) : (
          <section
            aria-label="Dados do usuário"
            className="w-full max-w-xl bg-(--surface-elevated) border border-gray-800/50 rounded-2xl p-6 flex flex-col gap-6"
          >
            <div className="flex items-center gap-4">
              <div
                aria-hidden="true"
                className="h-16 w-16 shrink-0 rounded-full bg-primary text-white text-xl font-semibold flex items-center justify-center"
              >
                {iniciais(usuario.nome)}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-white text-lg font-semibold truncate">{usuario.nome}</span>
                <span className="text-secondary text-sm truncate">{usuario.email}</span>
              </div>
            </div>

            <dl className="flex flex-col gap-4 border-t border-gray-800/50 pt-4 text-sm">
              <div className="flex flex-col gap-1">
                <dt className="text-secondary text-xs uppercase tracking-wider">Nome</dt>
                <dd className="text-white">{usuario.nome}</dd>
              </div>
              <div className="flex flex-col gap-1">
                <dt className="text-secondary text-xs uppercase tracking-wider">E-mail</dt>
                <dd className="text-white break-all">{usuario.email}</dd>
              </div>
              <div className="flex flex-col gap-1">
                <dt className="text-secondary text-xs uppercase tracking-wider">Perfil</dt>
                <dd className="text-white">{usuario.is_admin ? "Administrador" : "Product Owner (PO)"}</dd>
              </div>
            </dl>
          </section>
        )}

        {/* Logoff */}
        <section aria-label="Sessão" className="w-full max-w-xl flex flex-col gap-3">
          {erro && (
            <p role="alert" className="text-sm text-red-300">
              {erro}
            </p>
          )}
          <div>
            <button
              type="button"
              onClick={aoSair}
              disabled={saindo}
              className="h-10 px-4 rounded-lg flex items-center gap-2 text-sm font-medium text-red-400 border border-red-500/30 hover:bg-red-500/10 transition-colors disabled:opacity-50"
            >
              <LogOut size={16} />
              {saindo ? "Saindo..." : "Sair da conta"}
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}

export default Perfil