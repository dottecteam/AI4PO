"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PBI } from "@/app/types/api/pbi";
import { PbiContext } from "@/app/contexts/PbiContext";
import { pbiService } from "@/app/services/API/projeto/PBIService";

export default function PbiLayout({ children }: { children: React.ReactNode }) {
    const { pbiId } = useParams();
    const [pbi, setPbi] = useState<PBI | null>(null);
    const [carregando, setCarregando] = useState(true);

    useEffect(() => {
        pbiService.buscarPorId(Number(pbiId))
            .then(setPbi)
            .finally(() => setCarregando(false));
    }, [pbiId]);

    if (carregando) return <p className="text-white text-center">Carregando...</p>;
    if (!pbi) return <p className="text-white text-center">PBI não encontrado.</p>;

    return (
        <PbiContext.Provider value={{ pbi, setPbi }}>
            {children}
        </PbiContext.Provider>
    );
}
