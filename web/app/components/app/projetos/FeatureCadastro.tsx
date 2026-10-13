"use client";

import { featureService } from "@/app/services/API/projeto/FeatureService";
import { useEpicoAtual } from "@/app/contexts/EpicoContext";
import { useState } from "react";
import { InputLista } from "../../InputLista";

interface FeatureCadastroProps {
    aberto: boolean;
    onFechar: () => void;
    onCriado: () => void;
}

export default function FeatureCadastro({ aberto, onFechar, onCriado }: FeatureCadastroProps) {
    const epico = useEpicoAtual();

    const [titulo, setTitulo] = useState("");
    const [descricao, setDescricao] = useState("");
    const [objetivo, setObjetivo] = useState("");
    const [criteriosAceitacao, setCriteriosAceitacao] = useState<string[]>([]);
    const [avisoErro, setAvisoErro] = useState(false);


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


    async function cadastrarFeature() {
        if (!epico) return;

        if (!titulo || !descricao || !objetivo || !criteriosAceitacao) {
            setAvisoErro(true);
            return;
        }

        try {
            await featureService.criar({
                idEpico: epico.id,
                titulo,
                descricao,
                objetivo,
                criteriosAceitacao: criteriosAceitacao,
            });

            setTitulo("");
            setDescricao("");
            setObjetivo("");
            setCriteriosAceitacao([]);

            onFechar();
            onCriado();
        } catch (erro) {
            console.error("Erro ao cadastrar feature:", erro);
        }
    }

    if (!aberto) return null;

    return (
        <div className="fixed inset-0 z-50 max-h-screen flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-xl border border-gray-900 bg-[#080d16] shadow-2xl">

                {/* Header */}
                <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-800 bg-[#080d16] px-6 py-5">
                    <h2 className="font-semibold tracking-wider text-[#EF7541]">
                        Cadastrar Feature
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

                    {/* Critérios de aceitação */}
                    <div>
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
                    </div>
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
                        onClick={cadastrarFeature}
                        className="rounded-md bg-[#EF7541] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
                    >
                        Cadastrar
                    </button>

                </div>

            </div>
        </div >
    );
}