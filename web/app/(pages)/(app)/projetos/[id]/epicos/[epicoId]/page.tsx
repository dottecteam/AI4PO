'use client';

import Breadcrumb from "@/app/components/app/projetos/Breadcrumb";
import EpicoInfo from "@/app/components/app/projetos/EpicoInfo"
import TabelaFeatures from "@/app/components/app/projetos/TabelaFeatures";
import { useEpicoAtual } from "@/app/contexts/EpicoContext";

export default function PaginaEpico() {
    const epico = useEpicoAtual()

    if (!epico) return <p className="text-white text-center">Épico não encontrado.</p>;

    return (
        <main className="bg-[#010812] min-h-screen px-7 pt-10 pb-20 gap-5 flex flex-col text-white">
            <Breadcrumb />
            <EpicoInfo />
            <TabelaFeatures />
        </main>
    )
}