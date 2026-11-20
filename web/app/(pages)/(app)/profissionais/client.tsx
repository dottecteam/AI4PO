"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import Searchbar from "@/app/components/app/Searchbar"
import useDebounce from "@/app/hooks/useDebounce"
import { profissionalService } from "@/app/services/API/ProfissionalService"
import type { ProfissionalResumo } from "@/app/types/api/profissional"

export default function Profissionais() {
  const [profissionais, setProfissionais] = useState<ProfissionalResumo[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [termo, setTermo] = useState("")
  const termoComDebounce = useDebounce(termo, 300)

  useEffect(() => {
    let ativo = true

    profissionalService
      .listar(termoComDebounce)
      .then((dados) => {
        if (ativo) {
          setProfissionais(dados)
          setErro("")
        }
      })
      .catch(() => {
        if (ativo) setErro("Não foi possível carregar os profissionais.")
      })
      .finally(() => {
        if (ativo) setCarregando(false)
      })

    return () => {
      ativo = false
    }
  }, [termoComDebounce])

  return (
    <div className="w-full h-full flex flex-col flex-1 bg-background">
      <header className="w-full shrink-0 px-4 sm:px-6 lg:px-8 py-4 border-b border-gray-800/50 flex flex-col gap-3">
        <div>
          <h1 className="text-white font-semibold text-lg sm:text-2xl">Profissionais</h1>
          <p className="text-secondary text-xs sm:text-sm mt-1">
            Consulte os projetos, papéis e competências de cada profissional.
          </p>
        </div>
        <div className="max-w-md">
          <Searchbar
            valor={termo}
            onAtualizar={setTermo}
            placeholder="Buscar por nome, e-mail ou competência"
          />
        </div>
      </header>

      <main className="w-full flex-1 min-h-0 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6">
        {erro ? (
          <p role="alert" className="text-sm text-red-300">{erro}</p>
        ) : carregando ? (
          <p className="text-secondary text-sm">Carregando...</p>
        ) : profissionais.length === 0 ? (
          <p className="text-secondary text-sm">Nenhum profissional encontrado.</p>
        ) : (
          <ul className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {profissionais.map((profissional) => (
              <li key={profissional.id}>
                <Link
                  href={`/profissionais/${profissional.id}`}
                  className="h-full rounded-xl bg-(--surface-elevated) p-5 border border-transparent hover:bg-(--surface-base) hover:border-white flex flex-col gap-3"
                >
                  <div className="min-w-0">
                    <p className="text-white text-base font-semibold break-words">{profissional.nome}</p>
                    <p className="text-secondary text-xs break-all">{profissional.email}</p>
                  </div>

                  <div className="flex flex-wrap gap-1.5">
                    {profissional.competencias.length === 0 ? (
                      <span className="text-secondary text-xs">Sem competências cadastradas</span>
                    ) : (
                      profissional.competencias.map((competencia) => (
                        <span
                          key={competencia}
                          className="rounded-full bg-primary/10 border border-primary/20 px-2 py-0.5 text-xs text-primary"
                        >
                          {competencia}
                        </span>
                      ))
                    )}
                  </div>

                  <div className="mt-auto h-px bg-primary/60" />
                  <p className="text-xs text-secondary">
                    {profissional.total_projetos === 1
                      ? "1 projeto"
                      : `${profissional.total_projetos} projetos`}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}
