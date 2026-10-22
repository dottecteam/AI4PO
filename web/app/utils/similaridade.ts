export const MIN_CARACTERES_TEXTO_SIMILARIDADE = 40;
export const MIN_CARACTERES_QUERO_SIMILARIDADE = 15;

export interface CamposSimilaridade {
    titulo: string;
    como: string;
    quero: string;
    paraQue: string;
}

export function montarTextoSimilaridade(campos: CamposSimilaridade): string {
    const titulo = campos.titulo.trim();
    const como = campos.como.trim();
    const quero = campos.quero.trim();
    const paraQue = campos.paraQue.trim();

    return [
        titulo && `Título: ${titulo}`,
        como && `Como ${como}`,
        quero && `Quero ${quero}`,
        paraQue && `Para que ${paraQue}`,
    ].filter(Boolean).join("\n");
}
