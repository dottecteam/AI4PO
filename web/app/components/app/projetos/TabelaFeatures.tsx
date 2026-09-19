'use client';

import DropdownSection from "@/app/components/app/projetos/DropdownSection";
import { Epico } from "@/app/types/api/epico";
import { features } from "@/app/mock/features";
import { pbis } from "@/app/mock/pbis";
import { useRouter } from "next/navigation";

interface featuresProps {
    epico: Epico,
    projetoId: number
}

export default function TabelaFeatures({ epico, projetoId }: featuresProps) {
    const router = useRouter();
    const featureFiltradas = features.filter((feat) => feat.idEpico == epico.id)

    return (
        <DropdownSection label="Features">
            {/* Verifica se há features e cria a tabela */}
            {featureFiltradas.length > 0 ?
                (<table className="w-full text-left">
                    <thead>
                        <tr className="[&>*]:border-l-1 [&>*]:border-[#EF7541] [&>*]:py-1 [&>*]:px-2">
                            <th>Título</th>
                            <th>Criado em</th>
                            <th>PBIs</th>
                        </tr>
                    </thead>

                    <tbody className="[&>tr]:hover:bg-gray-900 [&>tr]:hover:cursor-pointer">
                        {featureFiltradas.map((feat) =>
                        (<tr key={feat.id}
                            className="[&>*]:px-2 border-b border-gray-700 hover:border-gray-500"
                            onClick={() => router.push(`/app/projetos/${projetoId}/epicos/${epico.id}/features/${feat.id}/`)}>
                            <td>{feat.titulo}</td>
                            <td>{new Date(feat.createdAt).toLocaleDateString('pt-BR')}</td>
                            <td>{pbis.filter((pbi) => pbi.idFeature == feat.id).length}</td>
                        </tr>))}
                    </tbody>
                </table>) : (
                    <p className="px-3 text-sm text-gray-500">Nenhuma feature registrada.</p>
                )}
        </DropdownSection>
    )
}