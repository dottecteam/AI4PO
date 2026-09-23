"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Epico } from "@/app/types/api/epico";
import { EpicoContext } from "@/app/contexts/EpicoContext";
import { epicoService } from "@/app/services/API/projeto/EpicoService";

export default function EpicoLayout({ children }: { children: React.ReactNode }) {
    const { epicoId } = useParams<{ epicoId: string }>();
    const [epico, setEpico] = useState<Epico | null>(null);
    const [carregando, setCarregando] = useState(true)

    useEffect(() => {
        epicoService.buscarPorId(Number(epicoId))
        .then(setEpico)
        .finally(() => setCarregando(false));
    }, [epicoId]);


    if (carregando) return <p className="text-white text-center">Carregando...</p>;
    if (!epico) return <p className="text-white text-center">Épico não encontrado.</p>;

    return (
        <EpicoContext.Provider value={{epico, setEpico}}>
            {children}
        </EpicoContext.Provider>
    );
}
