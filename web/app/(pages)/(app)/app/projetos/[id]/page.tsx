'use client';

import Breadcrumb from "@/app/components/app/projetos/Breadcrumb";
import ProjetoInfo from "@/app/components/app/projetos/ProjetoInfo";
import TabelaEpicos from "@/app/components/app/projetos/TabelaEpicos";
import { useProjetoAtual } from "@/app/contexts/ProjetoContext";

export default function PaginaProjeto() {
    const projeto = useProjetoAtual();

    if (!projeto) return <p className="text-white text-center">Projeto não encontrado.</p>;

    return (
        <main className="bg-[#010812] min-h-screen px-7 pt-10 pb-20 gap-5 flex flex-col text-white">
            <Breadcrumb />
            <ProjetoInfo/>
            <TabelaEpicos/>
        </main>
    );
}