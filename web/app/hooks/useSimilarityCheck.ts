"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import useDebounce from "@/app/hooks/useDebounce";
import { similarityService } from "@/app/services/API/SimilarityService";
import type { ResultadoSimilaridade } from "@/app/types/api/similaridade";
import {
    type CamposSimilaridade,
    MIN_CARACTERES_QUERO_SIMILARIDADE,
    MIN_CARACTERES_TEXTO_SIMILARIDADE,
    montarTextoSimilaridade,
} from "@/app/utils/similaridade";

export const SIMILARITY_DEBOUNCE_MS = 700;
export const MENSAGEM_ERRO_SIMILARIDADE =
    "A verificação de similaridade está temporariamente indisponível.";

export interface UseSimilarityCheckOptions extends CamposSimilaridade {
    ativo: boolean;
}

export interface UseSimilarityCheckResult {
    resultados: ResultadoSimilaridade[];
    carregando: boolean;
    atualizando: boolean;
    erro: string | null;
    limpar: () => void;
}

interface EstadoSimilaridade {
    texto: string;
    consultavel: boolean;
    status: "aguardando" | "concluido" | "cancelado";
    resultados: ResultadoSimilaridade[];
    erro: string | null;
}

export function useSimilarityCheck({
    titulo, como, quero, paraQue, ativo,
}: UseSimilarityCheckOptions): UseSimilarityCheckResult {
    const texto = useMemo(
        () => montarTextoSimilaridade({ titulo, como, quero, paraQue }),
        [titulo, como, quero, paraQue],
    );
    const consultavel = ativo &&
        texto.length >= MIN_CARACTERES_TEXTO_SIMILARIDADE &&
        quero.trim().length >= MIN_CARACTERES_QUERO_SIMILARIDADE;
    const entrada = useMemo(() => ({ texto, consultavel }), [texto, consultavel]);
    const entradaDebounced = useDebounce(entrada, SIMILARITY_DEBOUNCE_MS);
    const requestId = useRef(0);
    const controllerAtual = useRef<AbortController | null>(null);
    const [estado, setEstado] = useState<EstadoSimilaridade>({
        texto,
        consultavel,
        status: "aguardando",
        resultados: [],
        erro: null,
    });

    if (estado.texto !== texto || estado.consultavel !== consultavel) {
        setEstado({
            texto,
            consultavel,
            status: "aguardando",
            resultados: consultavel && estado.consultavel ? estado.resultados : [],
            erro: consultavel && estado.consultavel ? estado.erro : null,
        });
    }

    const cancelado = estado.status === "cancelado";

    useEffect(() => {
        const id = ++requestId.current;
        if (!entrada.consultavel || entrada !== entradaDebounced || cancelado) return;

        const controller = new AbortController();
        controllerAtual.current = controller;

        void similarityService.verificar(entrada.texto, controller.signal)
            .then(({ resultados }) => {
                if (controller.signal.aborted || id !== requestId.current) return;
                setEstado((anterior) => ({
                    ...anterior,
                    resultados,
                    erro: null,
                    status: "concluido",
                }));
            })
            .catch((erro: unknown) => {
                if (controller.signal.aborted || id !== requestId.current) return;
                const abortado = erro instanceof Error && erro.name === "AbortError";
                setEstado((anterior) => ({
                    ...anterior,
                    resultados: abortado ? anterior.resultados : [],
                    erro: abortado ? null : MENSAGEM_ERRO_SIMILARIDADE,
                    status: "concluido",
                }));
            });

        return () => {
            controller.abort();
            if (id === requestId.current) requestId.current += 1;
            if (controllerAtual.current === controller) controllerAtual.current = null;
        };
    }, [entrada, entradaDebounced, cancelado]);

    const limpar = useCallback(() => {
        requestId.current += 1;
        controllerAtual.current?.abort();
        controllerAtual.current = null;
        setEstado((anterior) => ({
            ...anterior,
            resultados: [],
            erro: null,
            status: "cancelado",
        }));
    }, []);

    const carregando = consultavel && entrada === entradaDebounced &&
        estado.status === "aguardando";

    return {
        resultados: consultavel ? estado.resultados : [],
        carregando,
        atualizando: carregando && estado.resultados.length > 0,
        erro: consultavel && !carregando ? estado.erro : null,
        limpar,
    };
}
