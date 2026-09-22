"use client";

import { useProjetoAtual, useSetProjetoAtual } from "@/app/contexts/ProjetoContext";
import { projetoService } from "@/app/services/API/projeto/ProjetoService";
import { ProjetoStatus, Projeto } from "@/app/types/api/projeto";
import { useEffect, useRef, useState } from "react";


export default function ProjetoInfo() {
    const [titulo, setTitulo] = useState(projeto.titulo);
    const [descricao, setDescricao] = useState(projeto.descricao);
    const [po, setPo] = useState(projeto.po);
    const [status, setStatus] = useState(projeto.status);

    return (
        <div className="mb-8 rounded-xl border border-gray-800 bg-[#080d16]">

            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5">
                <input
                    type="text"
                    value={titulo}
                    onChange={(e) => setTitulo(e.target.value)}
                    className="w-full max-w-3xl rounded-md border border-gray-700 bg-[#111827] px-3 py-2 text-2xl font-medium outline-none focus:border-[#EF7541]"
                />
            </div>

            {/* Informações */}
            <div className="px-6 py-6">

                {/* Dados principais */}
                <div className="mb-8 grid grid-cols-1 gap-x-8 gap-y-5 md:grid-cols-3">

                    {/* PO */}
                    <div>
                        <p className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
                            PO
                        </p>
                        <input
                            type="text"
                            value={po}
                            onChange={(e) => setPo(e.target.value)}
                            className="mt-1 w-full rounded-md border border-gray-700 bg-[#111827] px-2 py-2 text-sm outline-none focus:border-[#EF7541]"
                        />
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