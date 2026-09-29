import { useState, useRef, useEffect } from "react";

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

interface MenuFiltroProps {
    grupos: GrupoFiltro[];
    selecionados: Record<string, ValorFiltro[]>;
    onAtualizar: (chave: string, selecionados: ValorFiltro[]) => void;
}

export default function MenuFiltro({ grupos, selecionados, onAtualizar }: MenuFiltroProps) {
    const [aberto, setAberto] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClick(event: MouseEvent) {
            if (ref.current && !ref.current.contains(event.target as Node)) {
                setAberto(false);
            }
        }

        document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, []);

    function alternar(grupo: GrupoFiltro, valor: ValorFiltro) {
        const atuais = selecionados[grupo.chave] ?? [];

        if (grupo.multiplo === false) {
            onAtualizar(grupo.chave, [valor]);
            return;
        }

        const novo = atuais.includes(valor)
            ? atuais.filter((v) => v !== valor)
            : [...atuais, valor];

        onAtualizar(grupo.chave, novo);
    }

    return (
        <div ref={ref} className="relative text-white w-6 h-6">
            <button onClick={() => setAberto((atual) => !atual)}>
                {/* Trocado o text-[#EF7541] por text-primary */}
                <svg viewBox="0 0 23 21" fill="none" className="w-6 h-6 text-primary">
                    <path d="M21.25 1.25H1.25L9.25 10.71V17.25L13.25 19.25V10.71L21.25 1.25Z" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
            </button>

            {aberto && (
                <div className="absolute right-0 z-10 mt-2 w-max min-w-max rounded-md border border-primary-light bg-[var(--surface-elevated)] p-4 shadow-xl">
                    {grupos.map((grupo) => (
                        <div key={grupo.chave}>
                            <p className="font-semibold text-primary mb-1">
                                {grupo.rotulo}
                            </p>

                            <div className="flex flex-col gap-1 px-2">
                                {grupo.opcoes.map((opcao) => (
                                    <label
                                        key={String(opcao.valor)}
                                        className="flex w-max items-center gap-2 whitespace-nowrap"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={(selecionados[grupo.chave] ?? []).includes(opcao.valor)}
                                            onChange={() => alternar(grupo, opcao.valor)}
                                        />
                                        {opcao.rotulo}
                                    </label>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}