"use client";

import { useProjetoAtual } from "@/app/contexts/ProjetoContext";
import { epicoService } from "@/app/services/API/projeto/EpicoService";
import { useState } from "react";
import { InputLista } from "../../InputLista";

interface EpicoCadastroProps {
    aberto: boolean;
    onFechar: () => void;
    onCriado: () => void;
}

export default function EpicoCadastro({ aberto, onFechar, onCriado }: EpicoCadastroProps) {
    const projeto = useProjetoAtual();

    const [titulo, setTitulo] = useState("");
    const [descricao, setDescricao] = useState("");
    const [objetivo, setObjetivo] = useState("");
    const [resultadoEsperado, setResultadoEsperado] = useState("");
    const [escopoMacro, setEscopoMacro] = useState<string[]>([]);
    const [criteriosAceitacao, setCriteriosAceitacao] = useState<string[]>([]);
    const [avisoErro, setAvisoErro] = useState(false);

    function adicionarEscopoMacro() {
        setEscopoMacro((atuais) => [...atuais, ""]);
    }

    function alterarEscopoMacro(index: number, valor: string) {
        setEscopoMacro((atuais) =>
            atuais.map((escopo, i) =>
                i === index ? valor : escopo)
        );
    }

    function removerEscopoMacro(index: number) {
        setEscopoMacro((atuais) =>
            atuais.filter((_, i) => i !== index));
    }

    function adicionarCriterioAceitacao() {
        setCriteriosAceitacao((atuais) => [...atuais, ""]);
    }

    function alterarCriteriosAceitacao(index: number, valor: string) {
        setCriteriosAceitacao((atuais) =>
            atuais.map((criterio, i) =>
                i === index ? valor : criterio)
        );
    }

    function removerCriterioAceitacao(index: number) {
        setCriteriosAceitacao((atuais) =>
            atuais.filter((_, i) => i !== index)
        );
    }


    async function cadastrarEpico() {
        if (!projeto) return;

        if (!titulo || !descricao || !objetivo || !resultadoEsperado || !escopoMacro || !criteriosAceitacao) {
            setAvisoErro(true);
            return;
        }

        try {
            await epicoService.criar({
                idProjeto: projeto.id,
                titulo,
                descricao,
                objetivo,
                resultadoEsperado,
                escopoMacro: escopoMacro,
                criteriosAceitacao: criteriosAceitacao,
            });

            setTitulo("");
            setDescricao("");
            setObjetivo("");
            setResultadoEsperado("");
            setEscopoMacro([]);
            setCriteriosAceitacao([]);

            onFechar();
            onCriado();
        } catch (erro) {
            console.error("Erro ao cadastrar epico:", erro);
        }
    }

    if (!aberto) return null;

    return (
        <div className="fixed inset-0 z-50 max-h-screen flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-xl border border-gray-900 bg-[#080d16] shadow-2xl">

                {/* Header */}
                <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-800 bg-[#080d16] px-6 py-5">
                    <h2 className="font-semibold tracking-wider text-[#EF7541]">
                        Cadastrar Épico
                    </h2>

                    <button
                        onClick={onFechar}
                        className="flex size-9 items-center justify-center rounded-full text-gray-400 hover:bg-gray-800 hover:text-white"
                    >
                        <svg
                            viewBox="0 0 24 24"
                            className="h-6 w-6 rotate-45 text-[#EF7541]"
                            fill="none"
                        >
                            <path
                                d="M11.83 7.5v8.67M7.5 11.83h8.67M22.67 11.83a10.83 10.83 0 1 1-21.67 0 10.83 10.83 0 0 1 21.67 0Z"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        </svg>
                    </button>
                </div>

                {/* Formulário */}
                <div className="space-y-6 px-6 py-6">

                    {/* Título */}
                    <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            Título
                        </label>

                        <input
                            type="text"
                            value={titulo}
                            onChange={(e) => setTitulo(e.target.value)}
                            className="mt-1 w-full rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm text-gray-200 outline-none focus:border-[#EF7541]"
                        />
                    </div>

                    {/* Descrição */}
                    <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            Descrição
                        </label>

                        <textarea
                            value={descricao}
                            onChange={(e) => setDescricao(e.target.value)}
                            rows={4}
                            className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                        />
                    </div>

                    {/* Objetivo */}
                    <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            Objetivo
                        </label>

                        <textarea
                            value={objetivo}
                            onChange={(e) => setObjetivo(e.target.value)}
                            rows={3}
                            className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                        />
                    </div>

                    {/* Resultado esperado */}
                    <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            Resultado esperado
                        </label>

                        <textarea
                            value={resultadoEsperado}
                            onChange={(e) => setResultadoEsperado(e.target.value)}
                            rows={3}
                            className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                        />
                    </div>

                    {/* Escopo macro */}
                    <section>
                        <div className="mb-4 flex items-center border-l border-[#EF7541] pl-2">
                            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#EF7541]">
                                Escopo Macro
                            </h3>
                        </div>
                        <InputLista
                            rotuloItem="Capacidade Macro"
                            textoVazio="Nenhuma capacidade macro adicionada."
                            textoBotao="Adicionar Capacidade"
                            itens={escopoMacro}
                            onAdicionar={adicionarEscopoMacro}
                            onAlterar={alterarEscopoMacro}
                            onRemover={removerEscopoMacro} />
                    </section>

                    {/* Critérios de Aceitação */}
                    <section>
                        <div className="mb-4 flex items-center border-l border-[#EF7541] pl-2">
                            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#EF7541]">
                                Critérios de Aceitação
                            </h3>
                        </div>
                        <InputLista
                            rotuloItem="Critério"
                            textoVazio="Nenhum critério de aceitação adicionado."
                            textoBotao="Adicionar Critério"
                            itens={criteriosAceitacao}
                            onAdicionar={adicionarCriterioAceitacao}
                            onAlterar={alterarCriteriosAceitacao}
                            onRemover={removerCriterioAceitacao} />
                    </section>
                </div>

                {avisoErro && (
                    <p className="text-sm text-red-500 text-left px-6">Todos os campos devem ser preenchidos.</p>
                )}

                {/* Footer */}
                <div className="sticky bottom-0 flex justify-end gap-3 border-t border-gray-800 bg-[#080d16] px-6 py-4">

                    <button
                        onClick={onFechar}
                        className="rounded-md px-4 py-2 text-sm text-gray-300 hover:bg-gray-800"
                    >
                        Cancelar
                    </button>

                    <button
                        onClick={cadastrarEpico}
                        className="rounded-md bg-[#EF7541] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
                    >
                        Cadastrar
                    </button>

                </div>

            </div>
        </div >
    );
}