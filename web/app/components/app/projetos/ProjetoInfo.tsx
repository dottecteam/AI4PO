"use client";

import { useProjetoAtual, useSetProjetoAtual } from "@/app/contexts/ProjetoContext";
import { projetoService } from "@/app/services/API/projeto/ProjetoService";
import { ProjetoStatus } from "@/app/types/api/projeto";
import { useRouter } from "next/navigation"
import { useEffect, useRef, useState } from "react";


export default function ProjetoInfo() {
    const router = useRouter();

    const projeto = useProjetoAtual();
    if (!projeto) return <p className="text-white text-center">Projeto não encontrado.</p>;

    const setProjeto = useSetProjetoAtual();

    const [editando, setEditando] = useState(false);
    const [menuAberto, setMenuAberto] = useState(false);

    const [titulo, setTitulo] = useState(projeto.titulo);
    const [descricao, setDescricao] = useState(projeto.descricao);
    const [po, setPo] = useState(projeto.po);
    const [status, setStatus] = useState(projeto.status);

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

    async function confirmarEdicao() {
        try {
            const projetoAtualizado = await projetoService.editar(projeto!.id, { titulo, descricao, status });
            setProjeto?.(projetoAtualizado);
            setEditando(false);
        } catch (erro) {
            console.error("Erro ao editar projeto:", erro);
        }
    }

    function cancelarEdicao() {
        if (!projeto) return;

        try {
            setTitulo(projeto.titulo);
            setDescricao(projeto.descricao);
            setPo(projeto.po);
            setStatus(projeto.status);

            setEditando(false);
        } catch (erro) {
            console.log("Erro ao cancelar edição do projeto: ", erro);
        }
    }

    function excluirProjeto() {
        if (!projeto) return;

        try {
            setMenuAberto(false);
            projetoService.excluir(projeto.id);
            router.back();
        } catch (erro) {
            console.log("Erro ao excluir projeto: ", erro);
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
                            Projeto
                        </p>

                        <h1 className="text-2xl font-medium tracking-tight">
                            {titulo}
                        </h1>
                    </div>
                )}

                {/* Menu */}
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
                                onClick={excluirProjeto}
                                className="w-full px-4 py-3 text-left text-sm text-red-400 hover:bg-gray-800"
                            >
                                Excluir
                            </button>

                        </div>
                    )}

                </div>
            </div>

            {/* Informações */}
            <div className="px-6 py-6">

                {/* Dados principais */}
                <div className="mb-8 grid grid-cols-1 gap-x-8 gap-y-5 md:grid-cols-3">

                    {/* Status */}
                    <div>
                        <p className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            Status
                        </p>

                        {editando ? (
                            <select
                                value={status}
                                onChange={(e) =>
                                    setStatus(e.target.value as ProjetoStatus)
                                }
                                className="mt-1 w-full rounded-md border border-gray-700 bg-[#111827] px-2 py-2 text-sm outline-none focus:border-[#EF7541]"
                            >
                                <option value="Rascunho">Rascunho</option>
                                <option value="Ativo">Ativo</option>
                                <option value="Inativo">Inativo</option>
                            </select>
                        ) : (
                            <p className="mt-1 inline-block text-sm text-gray-200">
                                {status}
                            </p>
                        )}
                    </div>

                    {/* PO */}
                    <div>
                        <p className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            PO
                        </p>

                        {editando ? (
                            <input
                                type="text"
                                value={po}
                                onChange={(e) => setPo(e.target.value)}
                                className="mt-1 w-full rounded-md border border-gray-700 bg-[#111827] px-2 py-2 text-sm outline-none focus:border-[#EF7541]"
                            />
                        ) : (
                            <p className="mt-1 block text-sm text-gray-200">
                                {po}
                            </p>
                        )}
                    </div>

                    {/* Data */}
                    <div>
                        <p className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            Criado em
                        </p>

                        <p className="mt-1 block text-sm text-gray-200">
                            {new Date(projeto.createdAt).toLocaleDateString('pt-BR')}
                        </p>
                    </div>

                </div>

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
                            rows={6}
                            className="w-full resize-none rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                        />
                    ) : (
                        <p className="px-3 text-sm leading-6 text-gray-300">
                            {descricao}
                        </p>
                    )}
                </section>

            </div>

            {/* Footer de edição */}
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