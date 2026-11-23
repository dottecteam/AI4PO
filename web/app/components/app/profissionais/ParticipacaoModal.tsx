"use client"

import { useEffect, useState, type FormEvent } from "react"
import { mensagemDaApi, participacaoService } from "@/app/services/API/ProfissionalService"
import type { ParticipacaoPerfil, ProjetoGerenciavel } from "@/app/types/api/profissional"

// Mesmo limite do back (Participacao.papel)
const PAPEL_MAX = 100

type Props = {
  funcionarioId: number
  nomeProfissional: string
  projetos: ProjetoGerenciavel[]
  // Ausente = nova participação
  participacao?: ParticipacaoPerfil
  onFechar: () => void
  onSalvo: () => void
}

export default function ParticipacaoModal({
  funcionarioId,
  nomeProfissional,
  projetos,
  participacao,
  onFechar,
  onSalvo,
}: Props) {
  const editando = !!participacao
  const [projetoId, setProjetoId] = useState<number | "">(participacao?.projeto.id ?? "")
  const [papel, setPapel] = useState(participacao?.papel ?? "")
  const [erro, setErro] = useState("")
  const [enviando, setEnviando] = useState(false)

  // Garante que o projeto atual apareça na lista mesmo que não venha de projetos_gerenciaveis
  const opcoes =
    participacao && !projetos.some((p) => p.id === participacao.projeto.id)
      ? [{ id: participacao.projeto.id, titulo: participacao.projeto.titulo }, ...projetos]
      : projetos

  useEffect(() => {
    const aoTeclar = (evento: KeyboardEvent) => {
      if (evento.key === "Escape" && !enviando) onFechar()
    }
    window.addEventListener("keydown", aoTeclar)
    return () => window.removeEventListener("keydown", aoTeclar)
  }, [enviando, onFechar])

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault()
    if (enviando) return

    const papelLimpo = papel.trim()
    if (projetoId === "") return setErro("Selecione o projeto.")
    if (!papelLimpo) return setErro("Informe o papel do profissional no projeto.")
    if (papelLimpo.length > PAPEL_MAX) return setErro(`O papel pode ter no máximo ${PAPEL_MAX} caracteres.`)

    setEnviando(true)
    setErro("")
    try {
      if (participacao) {
        // Só manda o que mudou
        const mudancas: { projeto?: number; papel?: string } = {}
        if (projetoId !== participacao.projeto.id) mudancas.projeto = projetoId
        if (papelLimpo !== participacao.papel) mudancas.papel = papelLimpo
        if (Object.keys(mudancas).length === 0) {
          setErro("Nenhuma alteração para salvar.")
          setEnviando(false)
          return
        }
        await participacaoService.editar(participacao.id, mudancas)
      } else {
        await participacaoService.criar({ funcionario: funcionarioId, projeto: projetoId, papel: papelLimpo })
      }
      onSalvo()
    } catch (e) {
      setErro(mensagemDaApi(e))
      setEnviando(false)
    }
  }

  const classeCampo =
    "w-full h-11 bg-(--surface-elevated) outline-none rounded-xl px-4 text-sm text-white border border-gray-700/50 transition duration-200 focus:ring-2 focus:ring-primary"

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <form
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-participacao"
        onSubmit={enviar}
        noValidate
        className="w-full max-w-md bg-(--surface-base) border border-gray-800/50 rounded-2xl p-6 flex flex-col gap-4 shadow-2xl"
      >
        <div className="flex flex-col gap-1">
          <h2 id="titulo-participacao" className="text-white text-lg font-semibold">
            {editando ? "Editar participação" : "Adicionar participação"}
          </h2>
          <p className="text-secondary text-sm">
            {editando
              ? `Altere o projeto ou o papel de ${nomeProfissional}.`
              : `Vincule ${nomeProfissional} a um projeto que você gerencia.`}
          </p>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="participacao-projeto" className="text-sm text-white">
            Projeto
          </label>
          <select
            id="participacao-projeto"
            value={projetoId}
            onChange={(e) => {
              setProjetoId(e.target.value ? Number(e.target.value) : "")
              setErro("")
            }}
            className={classeCampo}
          >
            <option value="">Selecione um projeto</option>
            {opcoes.map((projeto) => (
              <option key={projeto.id} value={projeto.id}>
                {projeto.titulo}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="participacao-papel" className="text-sm text-white">
            Papel
          </label>
          <input
            id="participacao-papel"
            type="text"
            autoFocus
            autoComplete="off"
            maxLength={PAPEL_MAX}
            placeholder="Ex.: Desenvolvedor back-end"
            value={papel}
            onChange={(e) => {
              setPapel(e.target.value)
              setErro("")
            }}
            className={classeCampo}
          />
        </div>

        {erro && (
          <p role="alert" className="text-sm text-red-300">
            {erro}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onFechar}
            disabled={enviando}
            className="h-10 px-4 rounded-lg text-sm text-white border border-gray-700/50 hover:bg-(--surface-elevated) transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={enviando}
            className="h-10 px-4 rounded-lg text-sm font-medium text-white bg-primary hover:bg-primary-dark transition-colors disabled:opacity-50"
          >
            {enviando ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>
    </div>
  )
}
