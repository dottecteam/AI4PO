import { useMemo } from "react";

export function usePesquisaEFiltro<Item, Filtros>(
    itens: Item[],
    termo: string,
    combinaTermo: (item: Item, termo: string) => boolean,
    filtros: Filtros,
    combinaFiltros: (item: Item, filtros: Filtros) => boolean
) {
    return useMemo(
        () => itens.filter((item) => combinaTermo(item, termo) && combinaFiltros(item, filtros)),
        [itens, termo, filtros]
    );
}