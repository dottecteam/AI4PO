'use client';

import { Documento } from "@/app/types/api/documento"
import { useEffect, useRef, useState } from "react";

interface DocumentoCardProps {
    documento: Documento
}

export default function DocumentoCard({ documento, }: DocumentoCardProps) {
    const dataFormatada = new Date(documento.data).toLocaleDateString('pt-BR');

    const [menuAberto, setMenuAberto] = useState(false);
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

    function excluirDocumento() {
        console.log("Excluir documento", documento.nome)
    }

    return (
        <div className="w-full rounded-xl bg-[#212838] p-5 border border-transparent" key={documento.id}>
            {/* Header */}
            <div className="flex items-start justify-between">
                <span className={`rounded px-2 py-1 text-xs font-bold bg-[#EF7541]`}>
                    {documento.tipo}
                </span>

                {/* menu */}
                <div className="relative ml-4" ref={menuRef}>
                    <button
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
                    </button>

                    {menuAberto && (
                        <div className="absolute right-0 top-11 z-20 w-48 overflow-hidden rounded-lg border border-gray-700 bg-[#111827] shadow-xl">
                            <div className="border-t border-gray-700" />
                            <button
                                onClick={excluirDocumento}
                                className="w-full px-4 py-3 text-left text-sm text-red-400 hover:bg-gray-800"
                            >
                                Excluir
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Nome */}
            <p className="w-full py-1 text-lg text-white border-b-1 border-[#F7C09A]">{documento.nome}</p>

            {/* data */}
            <p className="text-sm text-white px-3 pt-2">{dataFormatada}</p>
        </div>
    )
}