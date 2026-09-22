"use client";

import { createContext, useContext, Dispatch, SetStateAction } from "react";
import { Feature } from "@/app/types/api/feature";

interface FeatureContextType {
    feature: Feature | null;
    setFeature: Dispatch<SetStateAction<Feature | null>>;
}

export const FeatureContext = createContext<FeatureContextType | null>(null);

export function useFeatureAtual() {
    const contexto = useContext(FeatureContext);
    return contexto?.feature ?? null;
}

export function useSetFeatureAtual() {
    const contexto = useContext(FeatureContext);
    return contexto?.setFeature;
}
