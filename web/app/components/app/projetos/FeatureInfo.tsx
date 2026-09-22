"use client";

import { useEpicoAtual } from "@/app/contexts/EpicoContext";
import { useFeatureAtual, useSetFeatureAtual } from "@/app/contexts/FeatureContext";
import { featureService } from "@/app/services/API/projeto/FeatureService";
import { Feature } from "@/app/types/api/feature";
import { useEffect, useRef, useState } from "react";

export default function FeatureInfo() {
    const feature = useFeatureAtual()
    const setFeature = useSetFeatureAtual()
    const epico = useEpicoAtual()
    if (!epico || !feature) return <p className="text-white text-center">Erro ao ler dados.</p>;

    const [editando, setEditando] = useState(false);
    const [menuAberto, setMenuAberto] = useState(false);

    const [titulo, setTitulo] = useState(feature.titulo);
    const [descricao, setDescricao] = useState(feature.descricao);
    const [objetivo, setObjetivo] = useState(feature.objetivo);
    const [criteriosAceitacao, setCriteriosAceitacao] = useState(
        feature.criteriosAceitacao
    );

    const menuRef = useRef<HTMLDivElement>(null);

    const dataFormatada = new Date(feature.createdAt).toLocaleDateString('pt-BR');

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
        if (!feature) return;

        try {
            setTitulo(feature.titulo);
            setDescricao(feature.descricao);
            setObjetivo(feature.objetivo);
            setCriteriosAceitacao(feature.criteriosAceitacao);

            setEditando(false);
        } catch (erro) {
            console.log("Erro ao cancelar edição de feature: ", erro)
        }
    }

    async function confirmarEdicao() {
        if (!feature) return;
        try {
            const featureAtualizada = await featureService.editar(feature.id, { titulo, descricao, objetivo, criteriosAceitacao });
            setFeature?.(featureAtualizada)
            setEditando(false);
        } catch (erro) {
            console.log("Erro ao confirmar edição de feature: ", erro)
        }
    }

    function excluirFeature() {
        if (!feature) return;
        try {
            setMenuAberto(false);
            console.log("Excluir feature:", feature.id);
        } catch (erro) {
            console.log("Erro ao excluir edição de feature: ", erro)
        }
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
                        <p className="text-xs font-semibold tracking-wider text-[#EF7541]">
                            Feature
                        </p>

                        <h1 className="text-2xl font-medium tracking-tight">
                            {titulo}
                        </h1>
                    </div>
                )}

                {/* Menu */}
                <div
                    className="relative ml-4"
                    ref={menuRef}
                >
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
                                onClick={excluirFeature}
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

                {/* Dados principais */}
                <div className="mb-8 grid grid-cols-1 gap-x-8 gap-y-5 md:grid-cols-2">

                    {/* Épico */}
                    <div>
                        <p className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            Épico
                        </p>

                        <p className="mt-1 block text-sm text-gray-200">
                            {epico.titulo}
                        </p>
                    </div>

                    {/* Criado em */}
                    <div>
                        <p className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            Criado em
                        </p>

                        <p className="mt-1 block text-sm text-gray-200">
                            {dataFormatada}
                        </p>
                    </div>

                </div>

                {/* Descrição, Objetivo e Critérios */}
                <div className="grid grid-cols-1 gap-8 md:grid-cols-2">

                    {/* Descrição */}
                    <section>
                        <div className="mb-2 flex items-center border-l border-[#EF7541] pl-2">
                            <h2 className="text-sm font-semibold uppercase tracking-wider text-[#EF7541]">
                                Descrição
                            </h2>
                        </div>

                        {editando ? (
                            <textarea
                                value={descricao}
                                onChange={(e) => setDescricao(e.target.value)}
                                rows={5}
                                className="w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                            />
                        ) : (
                            <p className="px-3 text-sm leading-6 text-gray-300">
                                {descricao}
                            </p>
                        )}
                    </section>

                    {/* Objetivo */}
                    <section>
                        <div className="mb-2 flex items-center border-l border-[#EF7541] pl-2">
                            <h2 className="text-sm font-semibold uppercase tracking-wider text-[#EF7541]">
                                Objetivo
                            </h2>
                        </div>

                        {editando ? (
                            <textarea
                                value={objetivo}
                                onChange={(e) => setObjetivo(e.target.value)}
                                rows={5}
                                className="w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                            />
                        ) : (
                            <p className="px-3 text-sm leading-6 text-gray-300">
                                {objetivo}
                            </p>
                        )}
                    </section>

                    {/* Critérios de Aceitação */}
                    <section className="md:col-p-2">
                        <div className="mb-2 flex items-center border-l border-[#EF7541] pl-2">
                            <h2 className="text-sm font-semibold uppercase tracking-wider text-[#EF7541]">
                                Critérios de Aceitação
                            </h2>
                        </div>

                        {editando ? (
                            <textarea
                                value={criteriosAceitacao.join("\n")}
                                onChange={(e) =>
                                    setCriteriosAceitacao(
                                        e.target.value.split("\n")
                                    )
                                }
                                rows={6}
                                className="w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                            />
                        ) : (
                            <ul className="px-3 text-sm leading-6 text-gray-300">
                                {criteriosAceitacao.map((criterio, index) => (
                                    <li key={index}>{criterio}</li>
                                ))}
                            </ul>
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