"use client";

import { ChevronDown, TriangleAlert } from "lucide-react";
import { useId, useState } from "react";
import type { ResultadoSimilaridade } from "@/app/types/api/similaridade";

interface SimilarityAlertProps {
    resultados: ResultadoSimilaridade[];
}

export default function SimilarityAlert({ resultados }: SimilarityAlertProps) {
    const titleId = useId();
    const resultsId = useId();
    const [expandido, setExpandido] = useState(false);
    const fontes = new Set<string>();
    const resultadosUnicos = resultados.filter((resultado) => {
        const fonte = `${resultado.projeto.id}:${resultado.documento.id}`;
        if (fontes.has(fonte)) return false;
        fontes.add(fonte);
        return true;
    });
    const count = resultadosUnicos.length;
    const descricao = count === 1
        ? "Encontramos 1 possível correspondência em conteúdo já indexado."
        : `Encontramos ${count} possíveis correspondências em conteúdos já indexados.`;

    function renderizarResultado(resultado: ResultadoSimilaridade) {
        return (
            <article className="min-w-0 rounded-md border border-gray-700/70 bg-[#111827] px-3 py-3">
                <dl className="grid min-w-0 grid-cols-1 gap-3 md:grid-cols-2">
                    <div className="min-w-0">
                        <dt className="text-xs font-semibold uppercase tracking-wider text-gray-500">Projeto</dt>
                        <dd className="break-words text-sm text-gray-200">{resultado.projeto.titulo}</dd>
                    </div>
                    <div className="min-w-0">
                        <dt className="text-xs font-semibold uppercase tracking-wider text-gray-500">Documento</dt>
                        <dd className="break-words text-sm text-gray-200">{resultado.documento.nome}</dd>
                    </div>
                </dl>
                <p className="mt-2 text-xs font-medium text-[var(--warning)]">
                    Similaridade textual: {Math.round(resultado.similaridade * 100)}%
                </p>
                <p className={`mt-2 break-words text-sm leading-6 text-gray-300 ${expandido ? "line-clamp-6" : "line-clamp-2"}`}>
                    {resultado.conteudo}
                </p>
            </article>
        );
    }

    return (
        <>
            {/* Keep the live region mounted before the first response arrives. */}
            <p className="sr-only" aria-live="polite" aria-atomic="true">
                {count > 0 ? `${count} possíveis correspondências encontradas.` : ""}
            </p>
            {count > 0 && (
                <aside aria-labelledby={titleId} className="mt-4 min-w-0 rounded-lg border border-[var(--warning)]/40 bg-[var(--warning)]/10 p-4">
                    <div className="flex items-start gap-3">
                        <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-[var(--warning)]/15 text-[var(--warning)]">
                            <TriangleAlert aria-hidden="true" size={18} strokeWidth={2} />
                        </span>
                        <div className="min-w-0">
                            <h3 id={titleId} className="text-sm font-semibold text-white">Possível conteúdo semelhante</h3>
                            <p className="mt-0.5 text-xs leading-5 text-gray-400">{descricao}</p>
                        </div>
                        <span aria-label={`${count} ${count === 1 ? "correspondência encontrada" : "correspondências encontradas"}`} className="ml-auto shrink-0 rounded-full bg-[var(--warning)]/15 px-2 py-0.5 text-xs font-semibold text-[var(--warning)]">
                            {count}
                        </span>
                    </div>

                    <div className="mt-3">{renderizarResultado(resultadosUnicos[0])}</div>

                    {count > 1 && (
                        <>
                            <button
                                type="button"
                                aria-expanded={expandido}
                                aria-controls={resultsId}
                                onClick={() => setExpandido((atual) => !atual)}
                                className="mt-2 flex min-h-11 w-full items-center justify-between gap-3 rounded-md px-3 py-2 text-left text-sm font-medium text-primary transition-colors duration-200 ease-in-out hover:bg-gray-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary motion-reduce:transition-none"
                            >
                                {expandido ? "Ocultar resultados" : `Ver mais ${count - 1} ${count === 2 ? "resultado" : "resultados"}`}
                                <ChevronDown aria-hidden="true" size={18} className={`shrink-0 transition-transform duration-200 ease-in-out motion-reduce:transition-none ${expandido ? "rotate-180" : ""}`} />
                            </button>
                            <div id={resultsId} hidden={!expandido} className="mt-2 space-y-2">
                                {resultadosUnicos.slice(1).map((resultado) => (
                                    <div key={`${resultado.projeto.id}:${resultado.documento.id}`}>
                                        {renderizarResultado(resultado)}
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </aside>
            )}
        </>
    );
}
