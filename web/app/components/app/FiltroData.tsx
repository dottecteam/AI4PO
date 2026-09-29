import { useState, useRef, useEffect } from "react";

interface FiltroDataProps {
    dataMin: string;
    dataMax: string;
    onAtualizar: (dataMin: string, dataMax: string) => void;
}

export default function FiltroData({ dataMin, dataMax, onAtualizar }: FiltroDataProps) {
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

    return (
        <div ref={ref} className="relative text-white w-6 h-6">
            <button onClick={() => setAberto((atual) => !atual)}>
                {/* text-[#EF7541] -> text-primary */}
                <svg viewBox="0 0 21 23" className="h-6 w-6 text-primary" fill="none">
                    <path d="M14.125 1.125V5.125M6.125 1.125V5.125M1.125 9.125H19.125M3.125 3.125H17.125C18.23 3.125 19.125 4.02 19.125 5.125V19.125C19.125 20.23 18.23 21.125 17.125 21.125H3.125C2.02 21.125 1.125 20.23 1.125 19.125V5.125C1.125 4.02 2.02 3.125 3.125 3.125Z" stroke="currentColor" strokeWidth="2.25" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
            </button>

            {aberto && (
                <div className="absolute right-0 mt-2 z-10 rounded-md border border-primary-light bg-[var(--surface-elevated)] p-4 flex flex-col gap-3 shadow-xl">
                    <label className="text-sm text-white flex flex-col gap-1">
                        De
                        <input type="date" value={dataMin} onChange={(e) => onAtualizar(e.target.value, dataMax)} className="bg-transparent border border-primary-light rounded px-2 py-1 text-white outline-none focus:border-primary" />
                    </label>
                    <label className="text-sm text-white flex flex-col gap-1">
                        Até
                        <input type="date" value={dataMax} onChange={(e) => onAtualizar(dataMin, e.target.value)} className="bg-transparent border border-primary-light rounded px-2 py-1 text-white outline-none focus:border-primary" />
                    </label>
                </div>
            )}
        </div>
    );
}