"use client"

import GrafoViewer from "@/app/components/app/graf/GrafoViewer"

export default function PaginaGrafoGlobal() {
  return (
    <main className="bg-[#010812] min-h-screen px-7 pt-10 pb-30 flex flex-col gap-5 text-white">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-wide text-[#EF7541]">
          Grafo Global
        </h1>
        <p className="text-sm text-gray-400">
          Todas as entidades e relações dos seus projetos em uma só teia de conhecimento.
        </p>
      </header>

      <GrafoViewer altura={640} />
    </main>
  )
}
