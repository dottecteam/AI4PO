import { ButtonHTMLAttributes, ReactNode } from "react"

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  loading?: boolean;
}

export function Button({ children, loading, ...rest }: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={loading || rest.disabled}
      className="mt-2 w-full cursor-pointer rounded-md bg-primary py-3 text-sm font-medium text-white transition-colors hover:bg-primary-dark disabled:cursor-not-allowed disabled:opacity-60"
    >
      {loading ? "Carregando..." : children}
    </button>
  );
}