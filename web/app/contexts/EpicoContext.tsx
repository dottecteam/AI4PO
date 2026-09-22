"use client";

import { createContext, useContext, Dispatch, SetStateAction } from "react";
import { Epico } from "@/app/types/api/epico";

interface EpicoContextType {
    epico: Epico | null;
    setEpico:  Dispatch<SetStateAction<Epico | null>>;
}

export const EpicoContext = createContext<EpicoContextType | null>(null);

export function useEpicoAtual() {
    const contexto = useContext(EpicoContext);
    return contexto?.epico ?? null;
}

export function useSetEpicoAtual() {
    const contexto = useContext(EpicoContext);
    return contexto?.setEpico;
}