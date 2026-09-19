'use client';

import DropdownSection from "@/app/components/app/projetos/DropdownSection";
import { Feature } from "@/app/types/api/feature";
import { pbis } from "@/app/mock/pbis";
import { useRouter } from "next/navigation";

interface featuresProps {
    feature: Feature,
    epicoId: number,
    projetoId: number
}

export default function TabelaPbis({ feature, epicoId, projetoId }: featuresProps) {
    const router = useRouter();
    const pbisFiltrados = pbis.filter((pbi) => pbi.idFeature == feature.id)
    return (
        <DropdownSection label="PBIs">
            {pbisFiltrados.length > 0 ? (<table className="w-full text-left">
                <thead>
                    <tr className="[&>*]:border-l-1 [&>*]:border-[#EF7541] [&>*]:py-1 [&>*]:px-2">
                        <th>Título</th>
                        <th>Criado em</th>
                    </tr>
                </thead>

                <tbody className="[&>tr]:hover:bg-gray-900 [&>tr]:hover:cursor-pointer">
                    {pbisFiltrados.map((pbi) =>
                    (<tr key={pbi.id}
                        className="[&>*]:px-2 border-b border-gray-700 hover:border-gray-500"
                        onClick={() => router.push(`/app/projetos/${projetoId}/epicos/${epicoId}/features/${feature.id}/pbis/${pbi.id}`)}>
                        <td>{pbi.titulo}</td>
                        <td>{new Date(pbi.createdAt).toLocaleDateString('pt-BR')}</td>
                    </tr>))}
                </tbody>
            </table>) : (
                <p className="px-3 text-sm text-gray-500">Nenhum Product Backlog Item registrado.</p>
            )}
        </DropdownSection>
    )
}