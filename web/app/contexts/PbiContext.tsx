"use client";

import { createContext, useContext, Dispatch, SetStateAction } from "react";
import { PBI } from "@/app/types/api/pbi";

interface PbiContextType {
    pbi: PBI | null;
    setPbi:  Dispatch<SetStateAction<PBI | null>>;
}

export const PbiContext = createContext<PbiContextType | null>(null);

export function usePbiAtual() {
    const contexto = useContext(PbiContext);
    return contexto?.pbi ?? null;
}

export function useSetPbicoAtual() {
    const contexto = useContext(PbiContext);
    return contexto?.setPbi;
}