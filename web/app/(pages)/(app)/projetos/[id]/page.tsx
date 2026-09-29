"use client"

import FiltroData from "@/app/components/app/FiltroData"
import MenuFiltro from "@/app/components/app/MenuFiltro"
import Breadcrumb from "@/app/components/app/projetos/Breadcrumb"
import DocumentoCard from "@/app/components/app/projetos/DocumentoCard"
import UploadDocumento from "@/app/components/app/projetos/UploadDocumento"
import DropdownSection from "@/app/components/app/projetos/DropdownSection"
import ProjetoInfo from "@/app/components/app/projetos/ProjetoInfo"
import TabelaEpicos from "@/app/components/app/projetos/TabelaEpicos"
import Searchbar from "@/app/components/app/Searchbar"
import { useProjetoAtual } from "@/app/contexts/ProjetoContext"
import useDebounce from "@/app/hooks/useDebounce"
import { usePesquisaEFiltro } from "@/app/hooks/usePesquisaEFiltro"
import { api } from "@/app/services/API/api"
import { Documento } from "@/app/types/api/documento"
import { useEffect, useState } from "react"

export default function PaginaProjeto() {
  const projeto = useProjetoAtual()

  const [documentos, setDocumentos] = useState<Documento[]>([])
  const [modalUploadAberto, setModalUploadAberto] = useState(false)

  async function carregarDocumentos() {
    if (!projeto) return
    try {
      const dados = await api.get<Documento[]>(
        `/api/projects/${projeto.id}/documents/`,
      )
      setDocumentos(dados)
    } catch (erro) {
      console.error("Falha ao carregar documentos", erro)
    }
  }

  useEffect(() => {
    carregarDocumentos()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projeto?.id])

  useEffect(() => {
    const temPendente = documentos.some(
      (d) => d.estado === "processando" || d.estado === "pendente",
    )
    if (!temPendente) return

    const intervalo = setInterval(carregarDocumentos, 3000)
    return () => clearInterval(intervalo)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentos])

  if (!projeto)
    return <p className="text-white text-center">Projeto não encontrado.</p>

  // Para aplicar nos filtros
  const tipoUnicos = Array.from(new Set(documentos.map((p) => p.tipo)))
  const opcoesTipos: OpcaoFiltro[] = tipoUnicos.map((s) => ({
    rotulo: s,
    valor: s,
  }))

  // Pesquisa
  const [termo, setTermo] = useState("")
  const termoComDebounce = useDebounce(termo, 300)

  // Filtro
  const [filtros, setFiltros] = useState<{
    tipo: ValorFiltro[]
    dataMin: string
    dataMax: string
  }>({
    tipo: tipoUnicos,
    dataMin: "",
    dataMax: "",
  })

  function atualizarFiltro(chave: string, novosSelecionados: ValorFiltro[]) {
    setFiltros((atual) => ({ ...atual, [chave]: novosSelecionados }))
  }

  function atualizarData(dataMin: string, dataMax: string) {
    setFiltros((atual) => ({ ...atual, dataMin, dataMax }))
  }
  const grupos: GrupoFiltro[] = [
    { chave: "tipo", rotulo: "Extensão", opcoes: opcoesTipos },
  ]

  const documentosFiltrados = usePesquisaEFiltro(
    documentos,
    termoComDebounce,
    (documento, termo) =>
      documento.nome.toLowerCase().includes(termo.toLowerCase()),
    filtros,
    (documento, filtros) => {
      const dataDocumento = documento.data.slice(0, 10)

      return (
        (filtros.tipo.length === 0 || filtros.tipo.includes(documento.tipo)) &&
        (!filtros.dataMin || dataDocumento >= filtros.dataMin) &&
        (!filtros.dataMax || dataDocumento <= filtros.dataMax)
      )
    },
  )

  return (
    <main className="bg-[#010812] min-h-screen px-7 pt-10 pb-30 gap-5 flex flex-col text-white">
      <Breadcrumb />
      <ProjetoInfo />
      <TabelaEpicos />

      {/* Documentos */}
      <DropdownSection
        label="Documentos"
        onAdd={() => setModalUploadAberto(true)}
      >
        <section className="flex flex-col gap-4">
          {/* Pesquisa e Filtragem */}
          <section className="w-full rounded-xl bg-[#212838] border border-transparent flex flex-even items-center gap-3 p-3">
            <Searchbar
              valor={termo}
              onAtualizar={setTermo}
              placeholder="Pesquise por nomes de documentos..."
            />
            <MenuFiltro
              grupos={grupos}
              selecionados={{ tipo: filtros.tipo }}
              onAtualizar={atualizarFiltro}
            />
            <FiltroData
              dataMin={filtros.dataMin}
              dataMax={filtros.dataMax}
              onAtualizar={atualizarData}
            />
          </section>

          {documentosFiltrados.length > 0 ? (
            ""
          ) : (
            <p className="text-white text-md text-center col-span-full">
              Nenhum documento registrado.
            </p>
          )}
          {documentosFiltrados.map((documento) => (
            <DocumentoCard
              documento={documento}
              key={documento.id}
              onReprocessado={carregarDocumentos}
            />
          ))}
        </section>
      </DropdownSection>

      <UploadDocumento
        aberto={modalUploadAberto}
        onFechar={() => setModalUploadAberto(false)}
        projetoId={projeto.id}
        onEnviado={carregarDocumentos}
      />
    </main>
  )
}
