"use client";

import Link from "next/link";
import { useProjetoAtual } from "@/app/contexts/ProjetoContext";
import { useEpicoAtual } from "@/app/contexts/EpicoContext";
import { useFeatureAtual } from "@/app/contexts/FeatureContext";

export default function Breadcrumb() {
    const projeto = useProjetoAtual();
    const epico = useEpicoAtual();
    const feature = useFeatureAtual();

    if (!projeto) return null;

    return (
        <nav className="flex items-center gap-1 text-sm text-[#AEC5F4] mb-4">
            <Link href="/app/projetos" className="hover:text-white hover:underline">
                Projetos
            </Link>

            <p className="text-[#EF7541]">/</p>
            <Link href={`/app/projetos/${projeto.id}`} className="hover:text-white hover:underline">
                {projeto.titulo}
            </Link>

            {epico && (
                <>
                    <p className="text-[#EF7541]">/</p>
                    <Link
                        href={`/app/projetos/${projeto.id}/epicos/${epico.id}`}
                        className="hover:text-white hover:underline"
                    >
                        {epico.titulo}
                    </Link>
                </>
            )}

            {feature && (
                <>
                    <p className="text-[#EF7541]">/</p>
                    <Link
                        href={`/app/projetos/${projeto.id}/epicos/${epico?.id}/features/${feature.id}`}
                        className="hover:text-white hover:underline"
                    >
                        {feature.titulo}
                    </Link>
                </>
            )}
        </nav>
    );
}
