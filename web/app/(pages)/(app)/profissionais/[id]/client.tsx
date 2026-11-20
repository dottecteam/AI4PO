"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { ArrowLeft } from "lucide-react"
import TrajetoriaProfissional from "@/app/components/app/profissionais/TrajetoriaProfissional"
import { profissionalService } from "@/app/services/API/ProfissionalService"
import type { PerfilProfissional } from "@/app/types/api/profissional"

// "Maria Souza Lima" -> "ML"; "Maria" -> "M"
function iniciais(nome: string) {
  const partes = nome.trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return "?"
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : ""
  return (partes[0][0] + ultima).toUpperCase()
}

export default function PerfilProfissionalPagina() {
  const { id } = useParams<{ id: string }>()
  const [perfil, setPerfil] = useState<PerfilProfissional | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")

  useEffect(() => {
    let ativo = true

    profissionalService
      .buscarPerfil(Number(id))
      .then((dados) => {
        if (ativo) {
          setPerfil(dados)
          setErro("")
        }
      })
      .catch(() => {
        if (ativo) setErro("Não foi possível carregar o perfil deste profissional.")
      })
      .finally(() => {
        if (ativo) setCarregando(false)
      })

    return () => {
      ativo = false
    }
  }, [id])

  return (
    <div className="w-full h-full flex flex-col flex-1 bg-background">
      <header className="w-full shrink-0 px-4 sm:px-6 lg:px-8 py-4 border-b border-gray-800/50">
        <Link
          href="/profissionais"
          className="inline-flex items-center gap-1.5 text-secondary text-xs hover:text-white transition-colors"
        >
          <ArrowLeft size={14} />
          Profissionais
        </Link>
        <h1 className="text-white font-semibold text-lg sm:text-2xl mt-1">Perfil do profissional</h1>
      </header>

      <main className="w-full flex-1 min-h-0 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6">
        {carregando ? (
          <p className="text-secondary text-sm">Carregando...</p>
        ) : erro || !perfil ? (
          <p role="alert" className="text-sm text-red-300">{erro}</p>
        ) : (
          <div className="w-full max-w-5xl mx-auto flex flex-col gap-6">
            <section
              aria-label="Dados do profissional"
              className="w-full rounded-2xl border border-gray-800/50 bg-(--surface-elevated) p-5 sm:p-6 flex items-center gap-4"
            >
              <div className="h-16 w-16 shrink-0 rounded-full bg-primary text-white flex items-center justify-center text-2xl font-semibold">
                {iniciais(perfil.nome)}
              </div>
              <div className="min-w-0">
                <h2 className="text-white text-xl font-bold break-words">{perfil.nome}</h2>
                <p className="text-secondary text-sm break-all">{perfil.email}</p>
              </div>
            </section>

            <TrajetoriaProfissional perfil={perfil} />
          </div>
        )}
      </main>
    </div>
  )
}
