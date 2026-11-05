"use client"

import Link from "next/link"
import { MessageSquare } from "lucide-react"

import AtividadesRecentes from "@/app/components/app/AtividadeRecente"
import DashboardCards from "@/app/components/app/DashboardCards"
import { useAuth } from "@/app/contexts/AuthContext"

export default function Dashboard() {
  const { usuario } = useAuth()

  return (
    <div className="w-full h-full flex flex-col bg-background">
      <header className="w-full shrink-0 flex justify-between items-center px-4 sm:px-6 lg:px-8 py-4 bg-background border-b border-gray-800/50 z-10">
        <div className="w-auto flex flex-col gap-1 min-w-0">
          <h1 className="text-white font-semibold text-lg sm:text-2xl lg:text-3xl truncate">
            Olá,{" "}
            <span className="text-primary">{usuario?.nome ?? "Usuário"}</span>
          </h1>
          <span className="hidden sm:inline text-xs sm:text-sm text-secondary">
            Plataforma de inteligência ativa e engenharia de PBIs.
          </span>
        </div>

        <Link
          href="/chatbot"
          className="h-10 ml-auto mr-2 px-3 rounded-lg flex items-center gap-2 shrink-0 bg-[var(--background)] hover:bg-[var(--surface-base)] transition-colors border border-gray-800/50"
        >
          <MessageSquare size={20} className="text-white" />
          <span className="text-white text-sm font-medium hidden sm:inline">
            Iniciar Nova Conversa
          </span>
        </Link>
      </header>

      <main className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-6 px-4 sm:px-6 lg:px-8 py-6">
        <DashboardCards />
        <AtividadesRecentes />
      </main>
    </div>
  )
}
