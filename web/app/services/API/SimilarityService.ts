import { api } from "@/app/services/API/api";
import type { RespostaSimilaridade } from "@/app/types/api/similaridade";

export const similarityService = {
    verificar: (texto: string, signal?: AbortSignal): Promise<RespostaSimilaridade> =>
        api.post<RespostaSimilaridade>("/api/similarity/", { texto }, { signal }),
};
