export interface ResultadoSimilaridade {
    chunkId: number;
    conteudo: string;
    similaridade: number;
    projeto: {
        id: number;
        titulo: string;
    };
    documento: {
        id: number;
        nome: string;
    };
}

export interface RespostaSimilaridade {
    resultados: ResultadoSimilaridade[];
}
