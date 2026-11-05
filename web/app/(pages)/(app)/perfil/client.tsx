"use client"

import { useState } from "react"
import {
  LogOut,
  Mail,
  UserRound,
  ShieldCheck,
  BriefcaseBusiness,
} from "lucide-react"

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
      await sair()
    } catch (e) {
      setErro(mensagemDeErro(e))
      setSaindo(false)
    }
  }

  return (
    <div className="w-full h-full flex flex-col flex-1 bg-background">
      <header className="w-full shrink-0 px-4 sm:px-6 lg:px-8 py-4 border-b border-gray-800/50">
        <h1 className="text-white font-semibold text-lg sm:text-2xl">
          Meu perfil
        </h1>
        <p className="text-secondary text-xs sm:text-sm mt-1">
          Gerencie suas informações e consulte os dados da sua conta.
        </p>
      </header>

      <main className="w-full flex-1 min-h-0 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6">
        {!usuario ? (
          <div
            role="alert"
            className="max-w-xl flex flex-col items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
          >
            <span>Não foi possível carregar seus dados.</span>

            <button
              type="button"
              onClick={() => window.location.reload()}
              className="h-9 px-4 rounded-lg bg-(--surface-elevated) text-white border border-gray-800/50 hover:bg-(--surface-base) transition-colors"
            >
              Tentar novamente
            </button>
          </div>
        ) : (
          <div className="w-full max-w-5xl mx-auto flex flex-col gap-6">
            <section
              aria-label="Perfil do usuário"
              className="w-full overflow-hidden rounded-2xl border border-gray-800/50 bg-(--surface-elevated)"
            >
              <div className="relative h-36 sm:h-48 overflow-hidden bg-gradient-to-br from-amber-600 via-orange-400 to-orange-600">
                <div className="absolute inset-0 opacity-20">
                  <div className="absolute -top-20 -right-10 h-64 w-64 rounded-full border-[30px] border-white" />
                  <div className="absolute -bottom-32 right-1/4 h-72 w-72 rounded-full border-[25px] border-white" />
                  <div className="absolute top-5 left-10 h-20 w-20 rounded-full bg-white/20 blur-2xl" />
                </div>

                <div className="absolute bottom-4 left-5 sm:left-8">
                  <span className="text-white/70 text-xs font-semibold uppercase tracking-[0.2em]">
                    AI4PO
                  </span>
                </div>
              </div>

              <div className="relative flex flex-col items-center px-4 pb-6">
                <div className="-mt-12 sm:-mt-14 relative z-10 h-24 w-24 sm:h-28 sm:w-28 shrink-0 rounded-full border-4 border-(--surface-elevated) bg-primary text-white flex items-center justify-center text-3xl sm:text-4xl font-semibold shadow-lg">
                  {iniciais(usuario.nome)}
                </div>

                <h2 className="mt-3 text-white text-xl sm:text-2xl font-bold text-center break-words">
                  {usuario.nome}
                </h2>

                <p className="text-secondary text-sm mt-1">{usuario.email}</p>

                <span className="mt-3 inline-flex items-center gap-2 rounded-full bg-primary/10 border border-primary/20 px-3 py-1 text-xs font-medium text-primary">
                  <ShieldCheck size={14} />
                  {usuario.is_admin ? "Administrador" : "Product Owner"}
                </span>
              </div>

              <div className="border-t border-gray-800/50 px-5 sm:px-8 py-3 flex items-center justify-center">
                <span className="text-secondary text-xs">
                  Informações da sua conta na plataforma
                </span>
              </div>
            </section>

            <section
              aria-label="Informações da conta"
              className="w-full flex flex-col gap-4"
            >
              <div>
                <h3 className="text-white font-semibold text-base">
                  Informações da conta
                </h3>
                <p className="text-secondary text-xs mt-1">
                  Dados associados ao seu usuário.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4 flex items-center gap-4">
                  <div className="h-10 w-10 shrink-0 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                    <UserRound size={19} />
                  </div>

                  <div className="min-w-0 flex flex-col gap-1">
                    <span className="text-secondary text-xs">
                      Nome completo
                    </span>
                    <span className="text-white text-sm font-medium break-words">
                      {usuario.nome}
                    </span>
                  </div>
                </div>

                <div className="rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4 flex items-center gap-4">
                  <div className="h-10 w-10 shrink-0 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                    <Mail size={19} />
                  </div>

                  <div className="min-w-0 flex flex-col gap-1">
                    <span className="text-secondary text-xs">
                      Endereço de e-mail
                    </span>
                    <span className="text-white text-sm font-medium break-all">
                      {usuario.email}
                    </span>
                  </div>
                </div>

                <div className="rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4 flex items-center gap-4 md:col-span-2">
                  <div className="h-10 w-10 shrink-0 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                    <BriefcaseBusiness size={19} />
                  </div>

                  <div className="min-w-0 flex flex-col gap-1">
                    <span className="text-secondary text-xs">
                      Tipo de acesso
                    </span>
                    <span className="text-white text-sm font-medium">
                      {usuario.is_admin
                        ? "Administrador da plataforma"
                        : "Product Owner (PO)"}
                    </span>
                  </div>
                </div>
              </div>
            </section>

            <section
              aria-label="Sessão"
              className="w-full rounded-xl border border-gray-800/50 bg-(--surface-elevated) p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
            >
              <div className="flex flex-col gap-1">
                <h3 className="text-white text-sm font-semibold">Sessão</h3>
                <p className="text-secondary text-xs">
                  Encerre sua sessão atual na plataforma.
                </p>
              </div>

              <div className="flex flex-col items-start sm:items-end gap-2">
                {erro && (
                  <p role="alert" className="text-sm text-red-300">
                    {erro}
                  </p>
                )}

                <button
                  type="button"
                  onClick={aoSair}
                  disabled={saindo}
                  className="h-10 px-4 rounded-lg flex items-center justify-center gap-2 text-sm font-medium text-red-400 border border-red-500/30 hover:bg-red-500/10 transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <LogOut size={16} />
                  {saindo ? "Saindo..." : "Sair da conta"}
                </button>
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default Perfil
