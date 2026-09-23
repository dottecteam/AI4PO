"use client";

import { usePbiAtual, useSetPbicoAtual } from "@/app/contexts/PbiContext";
import { pbis } from "@/app/mock/pbis";
import { pbiService } from "@/app/services/API/projeto/PBIService";
import { useRouter } from "next/navigation"
import { useEffect, useRef, useState } from "react";


export default function PBIInfo() {
    const router = useRouter();
    const pbi = usePbiAtual();
    const setPbi = useSetPbicoAtual();
    if (!pbi) return <p className="text-white text-center">PBI não encontrado.</p>;

    const [editando, setEditando] = useState(false);
    const [menuAberto, setMenuAberto] = useState(false);

    const [titulo, setTitulo] = useState(pbi.titulo);
    const [como, setComo] = useState(pbi.userStory.como);
    const [quero, setQuero] = useState(pbi.userStory.quero);
    const [paraQue, setParaQue] = useState(pbi.userStory.paraQue);
    const [regras, setRegras] = useState(pbi.regras ?? "");
    const [cenarios, setCenarios] = useState(pbi.cenarios);

    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (
                menuRef.current &&
                !menuRef.current.contains(event.target as Node)
            ) {
                setMenuAberto(false);
            }
        }

        document.addEventListener("mousedown", handleClickOutside);

        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    function iniciarEdicao() {
        setEditando(true);
        setMenuAberto(false);
    }

    function cancelarEdicao() {
        if (!pbi) return;
        try {
            setTitulo(pbi.titulo);
            setComo(pbi.userStory.como);
            setQuero(pbi.userStory.quero);
            setParaQue(pbi.userStory.paraQue);
            setRegras(pbi.regras ?? "");
            setCenarios(pbi.cenarios);

            setEditando(false);
        } catch (erro) {
            console.log("Erro ao cancelar edição de PBI: ", erro)
        }
    }

    async function confirmarEdicao() {
        if (!pbi) return;
        try {
            const pbiAtualizado = await pbiService.editar(pbi.id, { titulo, userStory: { como, quero, paraQue }, regras, cenarios });
            setPbi?.(pbiAtualizado);
            setEditando(false);
        } catch (erro) {
            console.log("Erro ao confirmar edição de PBI: ", erro)
        }
    }

    function excluirPBI() {
        if (!pbi) return;
        try {
            setMenuAberto(false);
            pbiService.excluir(pbi.id);
            router.back();
        } catch (erro) {
            console.log("Erro ao excluir PBI: ", erro)
        }
    }

    function alterarCenario(
        index: number,
        campo: "dado" | "quando" | "entao",
        valor: string
    ) {
        setCenarios((atuais) =>
            atuais.map((cenario, i) =>
                i === index
                    ? { ...cenario, [campo]: valor }
                    : cenario
            )
        );
    }

    function adicionarCenario() {
        setCenarios((atuais) => [
            ...atuais,
            {
                dado: "",
                quando: "",
                entao: "",
            },
        ]);
    }

    function removerCenario(index: number) {
        setCenarios((atuais) => atuais.filter((_, i) => i !== index));
    }

    return (
        <div className="mb-8 rounded-xl border border-gray-800 bg-[#080d16]">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5">
                {editando ? (
                    <input
                        type="text"
                        value={titulo}
                        onChange={(e) => setTitulo(e.target.value)}
                        className="w-full max-w-3xl rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-2xl font-medium outline-none focus:border-[#EF7541]"
                    />
                ) : (
                    <div>
                        <span className="text-xs font-semibold tracking-wider text-[#EF7541]">
                            Product Backlog Item
                        </span>

                        <h1 className="text-2xl font-medium tracking-tight">
                            {titulo}
                        </h1>
                    </div>
                )}

                <div className="relative ml-4" ref={menuRef}>
                    {!editando && (<button
                        onClick={() => setMenuAberto(!menuAberto)}
                        className="flex size-9 items-center justify-center rounded-full text-gray-400 hover:bg-gray-800 hover:text-white"
                    >
                        <svg
                            viewBox="0 0 24 24"
                            className="h-5 w-5"
                            fill="currentColor"
                        >
                            <circle cx="5" cy="12" r="1.5" />
                            <circle cx="12" cy="12" r="1.5" />
                            <circle cx="19" cy="12" r="1.5" />
                        </svg>
                    </button>)}

                    {menuAberto && (
                        <div className="absolute right-0 top-11 z-20 w-48 overflow-hidden rounded-lg border border-gray-700 bg-[#111827] shadow-xl">
                            <button
                                onClick={iniciarEdicao}
                                className="w-full px-4 py-3 text-left text-sm hover:bg-gray-800"
                            >
                                Editar
                            </button>

                            <div className="border-t border-gray-700" />

                            <button
                                onClick={excluirPBI}
                                className="w-full px-4 py-3 text-left text-sm text-red-400 hover:bg-gray-800"
                            >
                                Excluir
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Informações */}
            <div className="px-6 pb-6">
                <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
                    {/* User Story */}
                    <section className="md:col-span-2">
                        <div className="mb-4 flex items-center border-l border-[#EF7541] pl-2">
                            <h2 className="text-sm font-semibold uppercase tracking-wider text-[#EF7541]">
                                User Story
                            </h2>
                        </div>

                        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                            <div>
                                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                                    Como
                                </span>

                                {editando ? (
                                    <textarea
                                        value={como}
                                        onChange={(e) => setComo(e.target.value)}
                                        rows={3}
                                        className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                    />
                                ) : (
                                    <p className="mt-1 text-sm leading-6 text-gray-300">
                                        {como}
                                    </p>
                                )}
                            </div>

                            <div>
                                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                                    Quero
                                </span>

                                {editando ? (
                                    <textarea
                                        value={quero}
                                        onChange={(e) => setQuero(e.target.value)}
                                        rows={3}
                                        className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                    />
                                ) : (
                                    <p className="mt-1 text-sm leading-6 text-gray-300">
                                        {quero}
                                    </p>
                                )}
                            </div>

                            <div>
                                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                                    Para que
                                </span>

                                {editando ? (
                                    <textarea
                                        value={paraQue}
                                        onChange={(e) => setParaQue(e.target.value)}
                                        rows={3}
                                        className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                    />
                                ) : (
                                    <p className="mt-1 text-sm leading-6 text-gray-300">
                                        {paraQue}
                                    </p>
                                )}
                            </div>
                        </div>
                    </section>

                    {/* Cenários */}
                    <section className="md:col-span-2">
                        <div className="mb-4 flex items-center border-l border-[#EF7541] pl-2">
                            <h2 className="text-sm font-semibold uppercase tracking-wider text-[#EF7541]">
                                Cenários
                            </h2>
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

                                        {editando && (
                                            <button
                                                onClick={() =>
                                                    removerCenario(index)
                                                }
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
                                        )}
                                    </div>

                                    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                                        <div>
                                            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                                                Dado
                                            </span>

                                            {editando ? (
                                                <textarea
                                                    value={cenario.dado}
                                                    onChange={(e) =>
                                                        alterarCenario(
                                                            index,
                                                            "dado",
                                                            e.target.value
                                                        )
                                                    }
                                                    rows={3}
                                                    className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                                />
                                            ) : (
                                                <p className="mt-1 text-sm leading-6 text-gray-300">
                                                    {cenario.dado}
                                                </p>
                                            )}
                                        </div>

                                        <div>
                                            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                                                Quando
                                            </span>

                                            {editando ? (
                                                <textarea
                                                    value={cenario.quando}
                                                    onChange={(e) =>
                                                        alterarCenario(
                                                            index,
                                                            "quando",
                                                            e.target.value
                                                        )
                                                    }
                                                    rows={3}
                                                    className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                                />
                                            ) : (
                                                <p className="mt-1 text-sm leading-6 text-gray-300">
                                                    {cenario.quando}
                                                </p>
                                            )}
                                        </div>

                                        <div>
                                            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                                                Então
                                            </span>

                                            {editando ? (
                                                <textarea
                                                    value={cenario.entao}
                                                    onChange={(e) =>
                                                        alterarCenario(
                                                            index,
                                                            "entao",
                                                            e.target.value
                                                        )
                                                    }
                                                    rows={3}
                                                    className="mt-1 w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                                                />
                                            ) : (
                                                <p className="mt-1 text-sm leading-6 text-gray-300">
                                                    {cenario.entao}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {editando && (
                                <button
                                    onClick={adicionarCenario}
                                    className="rounded-md border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800"
                                >
                                    Adicionar cenário
                                </button>
                            )}

                            {!editando && cenarios.length === 0 && (
                                <p className="text-sm text-gray-500">
                                    Nenhum cenário informado.
                                </p>
                            )}
                        </div>
                    </section>

                    {/* Regras */}
                    <section className="md:col-span-2">
                        <div className="mb-2 flex items-center border-l border-[#EF7541] pl-2">
                            <h2 className="text-sm font-semibold uppercase tracking-wider text-[#EF7541]">
                                Regras
                            </h2>
                        </div>

                        {editando ? (
                            <textarea
                                value={regras}
                                onChange={(e) => setRegras(e.target.value)}
                                rows={5}
                                className="w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                            />
                        ) : regras ? (
                            <p className="px-3 text-sm leading-6 text-gray-300 whitespace-pre-line">
                                {regras}
                            </p>
                        ) : (
                            <p className="px-3 text-sm text-gray-500">
                                Nenhuma regra informada.
                            </p>
                        )}
                    </section>
                </div>
            </div>

            {/* Footer */}
            {editando && (
                <div className="flex justify-end gap-3 px-6 py-4">
                    <button
                        onClick={cancelarEdicao}
                        className="rounded-md px-4 py-2 text-sm text-gray-300 hover:bg-gray-800"
                    >
                        Cancelar
                    </button>

                    <button
                        onClick={confirmarEdicao}
                        className="rounded-md bg-[#EF7541] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
                    >
                        Confirmar
                    </button>
                </div>
            )}
        </div>
    );
}