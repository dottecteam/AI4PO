import Link from "next/link";
import { SearchX } from "lucide-react";
import type { Metadata } from "next";
import { Button } from "@/app/components/ui/Button";

export const metadata: Metadata = {
    title: "Página não encontrada | AI4PO",
};

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-background p-6">
            <div className="flex flex-col items-center text-center w-full max-w-md bg-[var(--surface-elevated)] p-10 rounded-2xl border border-gray-800/50 shadow-2xl">
                <SearchX size={64} className="text-primary mb-6 animate-pulse" strokeWidth={1.5} />
                
                <h1 className="text-6xl font-black text-primary tracking-tighter">
                    404
                </h1>
                <h2 className="text-2xl font-bold mt-4 text-white">
                    Página não encontrada
                </h2>
                
                <p className="text-[var(--foreground-muted)] mt-3 mb-4 leading-relaxed">
                    Ops! O conteúdo que você está procurando não existe, foi movido ou você não tem permissão para acessá-lo.
                </p>
                
                {/* Envolvendo o botão com o Link para manter o roteamento rápido */}
                <Link href="/" className="w-full block">
                    <Button type="button">
                        Voltar para o Início
                    </Button>
                </Link>
            </div>
        </div>
    );
}