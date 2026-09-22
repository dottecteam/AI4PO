"use client";

import { createContext, useContext, Dispatch, SetStateAction } from "react";
import { Projeto } from "@/app/types/api/projeto";

interface ProjetoContextType {
    projeto: Projeto | null;
    setProjeto: Dispatch<SetStateAction<Projeto | null>>;
}

export const ProjetoContext = createContext<ProjetoContextType | null>(null);

export function useProjetoAtual() {
    const contexto = useContext(ProjetoContext);
    return contexto?.projeto ?? null;
}

export function useSetProjetoAtual() {
    const contexto = useContext(ProjetoContext);
    return contexto?.setProjeto;
}