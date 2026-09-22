export interface Epico {
    id: number;
    idProjeto: number;
    titulo: string;
    descricao: string;
    objetivo: string;
    escopoMacro: string[];
    resultadoEsperado: string;
    criteriosAceitacao: string[];
    createdAt: string;
}

export interface EpicoInput {
    idProjeto: number;
    titulo: string;
    descricao: string;
    objetivo: string;
    escopoMacro: string[];
    resultadoEsperado: string;
    criteriosAceitacao: string[];
}