"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Feature } from "@/app/types/api/feature";
import { FeatureContext } from "@/app/contexts/FeatureContext";
import { featureService } from "@/app/services/API/projeto/FeatureService";

export default function FeatureLayout({ children }: { children: React.ReactNode }) {
    const { featureId } = useParams<{ featureId: string }>();
    const [feature, setFeature] = useState<Feature | null>(null);
    const [carregando, setCarregando] = useState(true)

    useEffect(() => {
        featureService.buscarPorId(Number(featureId))
        .then(setFeature)
        .finally(() => setCarregando(false));
    }, [featureId]);
    
    if (carregando) return <p className="text-white text-center">Carregando...</p>;
    if (!feature) return <p className="text-white text-center">Feature não encontrada.</p>;

    return (
        <FeatureContext.Provider value={{feature, setFeature}}>
            {children}
        </FeatureContext.Provider>
    );
}
