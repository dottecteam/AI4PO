type ValorFiltro = string | number;

interface OpcaoFiltro {
    rotulo: string;
    valor: ValorFiltro;
}

interface GrupoFiltro {
    chave: string;
    rotulo: string;
    opcoes: OpcaoFiltro[];
    multiplo?: boolean;
}