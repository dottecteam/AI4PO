'use client';

import Breadcrumb from "@/app/components/app/projetos/Breadcrumb";
import DocumentoCard from "@/app/components/app/projetos/DocumentoCard";
import DropdownSection from "@/app/components/app/projetos/DropdownSection";
import ProjetoInfo from "@/app/components/app/projetos/ProjetoInfo";
import TabelaEpicos from "@/app/components/app/projetos/TabelaEpicos";
import { useProjetoAtual } from "@/app/contexts/ProjetoContext";
import { documentosMock } from "@/app/mock/documentos";

export default function PaginaProjeto() {
    const projeto = useProjetoAtual();
    if (!projeto) return <p className="text-white text-center">Projeto não encontrado.</p>;

    const documentos = documentosMock

    function uploadDocumento() {
        console.log("adicionando documento")
    }

    return (
        <main className="bg-[#010812] min-h-screen px-7 pt-10 pb-20 gap-5 flex flex-col text-white">
            <Breadcrumb />
            <ProjetoInfo />
            <TabelaEpicos />

            {/* Documentos */}
            <DropdownSection label="Documentos" onAdd={() => uploadDocumento()}>
                <section className="flex flex-col gap-4">
                    {documentos.length > 0 ? "" : (<p className="text-white text-md text-center col-span-full">Nenhum documento registrado.</p>)}
                    {documentos.map((documento) =>
                        (<DocumentoCard documento={documento} />)
                    )}
                </section>
            </DropdownSection>
        </main>
    );
}