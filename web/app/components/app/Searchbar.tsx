interface SearchbarProps {
    valor: string;
    onAtualizar: (valor: string) => void;
    placeholder?: string;
    className?: string;
    estiloInput?: string;
}

export default function Searchbar({ valor, onAtualizar, placeholder, className, estiloInput }: SearchbarProps) {
    return (
        <div className={className ?? "flex items-center w-full rounded-lg border border-primary-light bg-[var(--surface-base)] focus-within:border-primary transition-colors"}>
            <svg viewBox="0 0 14 14" className="h-4 w-4 ml-3 shrink-0 text-primary" fill="none">
                <path d="M13 13L10.107 10.107M11.667 6.333A5.333 5.333 0 1 1 1 6.333a5.333 5.333 0 0 1 10.667 0Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <input
                type="text"
                value={valor}
                onChange={(e) => onAtualizar(e.target.value)}
                placeholder={placeholder}
                className={estiloInput ?? "w-full px-3 py-2 text-white bg-transparent outline-none placeholder:text-[var(--foreground-muted)]"}
            />
        </div>
    );
}