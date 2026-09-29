"use client";

import { useFeatureAtual } from "@/app/contexts/FeatureContext";
import { pbiService } from "@/app/services/API/projeto/PBIService";
import { useState } from "react";

interface Cenario {
    dado: string;
    quando: string;
    entao: string;
}

interface PbiCadastroProps {
    aberto: boolean;
    onFechar: () => void;
}

export default function PbiCadastro({ aberto, onFechar }: PbiCadastroProps) {
    const feature = useFeatureAtual();

    const [titulo, setTitulo] = useState("");
    const [como, setComo] = useState("");
    const [quero, setQuero] = useState("");
    const [paraQue, setParaQue] = useState("");
    const [regras, setRegras] = useState("");
    const [cenarios, setCenarios] = useState<Cenario[]>([]);
    const [avisoErro, setAvisoErro] = useState(false);

    function alterarCenario(
        index: number,
        campo: "dado" | "quando" | "entao",
        valor: string
    ) {
        setCenarios((atuais) =>
            atuais.map((cenario, i) =>
                i === index ? { ...cenario, [campo]: valor } : cenario
            )
        );
    }

    function adicionarCenario() {
        setCenarios((atuais) => [
            ...atuais,
            { dado: "", quando: "", entao: "" },
        ]);
    }

    function removerCenario(index: number) {
        setCenarios((atuais) => atuais.filter((_, i) => i !== index));
    }

    async function cadastrarPbi() {
        if (!feature) return;

        if (!titulo || !como || !quero || !paraQue) {
            setAvisoErro(true);
            return;
        }

        try {
            await pbiService.criar({
                idFeature: feature.id,
                titulo,
                userStory: { como, quero, paraQue },
                regras,
                cenarios,
            });

            setTitulo("");
            setComo("");
            setQuero("");
            setParaQue("");
            setRegras("");
            setCenarios([]);
            setAvisoErro(false);

            onFechar();
        } catch (erro) {
            console.error("Erro ao cadastrar pbi:", erro);
        }
    }

    if (!aberto) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
            <div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-xl border border-gray-900 bg-[#080d16] shadow-2xl">

                {/* Header */}
                <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-800 bg-[#080d16] px-6 py-5">
                    <h2 className="font-semibold tracking-wider text-[#EF7541]">
                        Cadastrar PBI
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

                    {/* User Story */}
                    <section>
                        <div className="mb-4 flex items-center border-l border-[#EF7541] pl-2">
                            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#EF7541]">
                                User Story
                            </h3>
                        </div>

                        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                            <div>
                                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                                    Como
                                </label>

                                <textarea
                                    value={como}
                                    onChange={(e) => setComo(e.target.value)}
                                    rows={3}
                                    className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                                    Quero
                                </label>

                                <textarea
                                    value={quero}
                                    onChange={(e) => setQuero(e.target.value)}
                                    rows={3}
                                    className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                                    Para que
                                </label>

                                <textarea
                                    value={paraQue}
                                    onChange={(e) => setParaQue(e.target.value)}
                                    rows={3}
                                    className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                />
                            </div>
                        </div>
                    </section>

                    {/* Cenários */}
                    <section>
                        <div className="mb-4 flex items-center border-l border-[#EF7541] pl-2">
                            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#EF7541]">
                                Cenários
                            </h3>
                        </div>

                        <div className="space-y-4">
                            {cenarios.map((cenario, index) => (
                                <div
                                    key={index}
                                    className="rounded-lg border border-gray-800 p-4"
                                >
                                    <div className="mb-4 flex items-center justify-between">
                                        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                                            Cenário {index + 1}
                                        </span>

                                        <button
                                            onClick={() => removerCenario(index)}
                                            className="size-5 m-1 flex justify-center items-center hover:bg-black hover:opacity-70 hover:cursor-pointer rounded-full"
                                        >
                                            <svg
                                                viewBox="0 0 14 15"
                                                className="h-4 w-4 text-[#EF7541]"
                                                fill="none"
                                            >
                                                <path
                                                    d="M0.8 3.467H12.8M2.133 3.467V12.8A1.333 1.333 0 0 0 3.467 14.133H10.133A1.333 1.333 0 0 0 11.467 12.8V3.467M4.133 3.467V2.133A1.333 1.333 0 0 1 5.467 0.8H8.133A1.333 1.333 0 0 1 9.467 2.133V3.467"
                                                    stroke="currentColor"
                                                    strokeWidth="1.6"
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                />
                                            </svg>
                                        </button>
                                    </div>

                                    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                                        <div>
                                            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                                                Dado
                                            </label>

                                            <textarea
                                                value={cenario.dado}
                                                onChange={(e) =>
                                                    alterarCenario(index, "dado", e.target.value)
                                                }
                                                rows={3}
                                                className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                                                Quando
                                            </label>

                                            <textarea
                                                value={cenario.quando}
                                                onChange={(e) =>
                                                    alterarCenario(index, "quando", e.target.value)
                                                }
                                                rows={3}
                                                className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                                                Então
                                            </label>

                                            <textarea
                                                value={cenario.entao}
                                                onChange={(e) =>
                                                    alterarCenario(index, "entao", e.target.value)
                                                }
                                                rows={3}
                                                className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}

                            <button
                                onClick={adicionarCenario}
                                className="rounded-md border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800"
                            >
                                Adicionar cenário
                            </button>

                            {cenarios.length === 0 && (
                                <p className="text-sm text-gray-500">
                                    Nenhum cenário adicionado.
                                </p>
                            )}
                        </div>
                    </section>

                    {/* Regras/observações */}
                    <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            Regras / observações
                        </label>

                        <textarea
                            value={regras}
                            onChange={(e) => setRegras(e.target.value)}
                            rows={4}
                            className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                        />
                    </div>

                </div>

                {avisoErro && (
                    <p className="text-sm text-red-500 text-left px-6">Título e user story devem ser preenchidos.</p>
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
                        onClick={cadastrarPbi}
                        className="rounded-md bg-[#EF7541] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
                    >
                        Cadastrar
                    </button>

                </div>

            </div>
        </div>
    );
}