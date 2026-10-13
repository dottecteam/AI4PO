interface SecaoListaProps {
    rotuloItem: string;
    textoVazio: string;
    textoBotao: string;
    itens: string[];
    onAdicionar: () => void;
    onRemover: (index: number) => void;
    onAlterar: (index: number, valor: string) => void;
}

export function InputLista({
    rotuloItem,
    textoVazio,
    textoBotao,
    itens,
    onAdicionar,
    onRemover,
    onAlterar,
}: SecaoListaProps) {
    return (
        <div>
            <div className="space-y-4">
                {itens.map((item, index) => (
                    <div key={index}>
                        <div className="mb-1 flex items-center justify-between">
                            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                                {rotuloItem} {index + 1}
                            </span>

                            <button
                                type="button"
                                onClick={() => onRemover(index)}
                                className="size-4 flex justify-center items-center hover:bg-black hover:opacity-70 hover:cursor-pointer rounded-full"
                            >
                                <svg viewBox="0 0 14 15" className="h-4 w-4 text-[#EF7541]" fill="none">
                                    <path
                                        d="M0.8 3.467H12.8M2.133 3.467V12.8A1.333 1.333 0 0 0 3.467 14.133H10.133A1.333 1.333 0 0 0 11.467 12.8V3.467M4.133 3.467V2.133A1.333 1.333 0 0 1 5.467 0.8H8.133A1.333 1.333 0 0 1 9.467 2.133V3.467"
                                        stroke="currentColor"
                                        strokeWidth="1.6"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                </svg>
                            </button>
                        </div>

                        <textarea
                            value={item}
                            onChange={(e) => onAlterar(index, e.target.value)}
                            className="mt-1 w-full rounded-md border border-gray-700 bg-[#111827] px-2 py-1 text-sm leading-6 text-gray-200 outline-none focus:border-[#EF7541]"
                        />
                    </div>
                ))}
            </div>

            {itens.length === 0 && (
                <p className="text-sm text-gray-500">{textoVazio}</p>
            )}

            <button
                type="button"
                onClick={onAdicionar}
                className="rounded-md border border-gray-700 px-2 py-1 text-sm text-gray-300 hover:bg-gray-800"
            >
                {textoBotao}
            </button>
        </div>
    );
}