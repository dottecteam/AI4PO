"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Projeto } from "@/app/types/api/projeto";
import { ProjetoContext } from "@/app/contexts/ProjetoContext";
import { projetosService } from "@/app/services/API/projeto/ProjetoService";
export default function ProjetoLayout({ children }: { children: React.ReactNode }) {
    const { id } = useParams<{ id: string }>();
    const [projeto, setProjeto] = useState<Projeto | null>(null);
    const [carregando, setCarregando] = useState(true)

    useEffect(() => {
        projetosService.buscarPorId(Number(id))
            .then(setProjeto)
            .finally(() => setCarregando(false));
    }, [id]);

    if (carregando) return <p className="text-white text-center">Carregando...</p>;
    if (!projeto) return <p className="text-white text-center">Projeto não encontrado.</p>;

    return (
        <ProjetoContext.Provider value={{ projeto, setProjeto }}>
            {children}
        </ProjetoContext.Provider>
    );
}
