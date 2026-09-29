'use client';

import Breadcrumb from "@/app/components/app/projetos/Breadcrumb";
import FeatureInfo from "@/app/components/app/projetos/FeatureInfo";
import TabelaPbis from "@/app/components/app/projetos/TabelaPbis";
import { useFeatureAtual } from "@/app/contexts/FeatureContext";

export default function PaginaFeature() {
    const feature = useFeatureAtual()
    if (!feature) return <p className="text-white text-center">Feature não encontrada.</p>;

    return (
        <main className="bg-[#010812] min-h-screen px-7 pt-10 pb-20 gap-5 flex flex-col text-white">
            <Breadcrumb />
            <FeatureInfo />
            <TabelaPbis />
        </main>
    )
}