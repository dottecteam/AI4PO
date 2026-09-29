"use client"
import { Eye, EyeOff } from "lucide-react"
import { InputHTMLAttributes, useState } from "react"

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function Input({ label, error, type = "text", id, ...rest }: InputProps) {
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const isPassword = type === "password";
  const currentType = isPassword && mostrarSenha ? "text" : type;

  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="text-sm font-medium text-primary">
          {label}
        </label>
        {isPassword && (
          <a href="#" className="text-sm text-primary hover:underline">
            Esqueceu a senha?
          </a>
        )}
      </div>
      <div className="relative">
        <input
          id={id}
          type={currentType}
          className={`w-full rounded-md border bg-[var(--surface-base)] px-4 py-3 text-sm text-white placeholder:text-white/40 outline-none transition-colors
            ${error ? "border-red-500 focus:border-red-500" : "border-primary-light focus:border-primary"}
            ${isPassword ? "pr-11" : ""}
          `}
          {...rest}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setMostrarSenha((v) => !v)}
            aria-label={mostrarSenha ? "Ocultar senha" : "Mostrar senha"}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--foreground-muted)] hover:text-white transition-colors"
          >
            {mostrarSenha ? <EyeOff size={20} /> : <Eye size={20} />}
          </button>
        )}
      </div>
      {error && <span className="text-xs text-red-500">{error}</span>}
    </div>
  );
}