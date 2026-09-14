'use client';

import DropdownSection from "@/app/components/app/projetos/DropdownSection";
import { Projeto } from "@/app/types/api/projetos";
import { useRouter } from "next/navigation";

interface epicosProps {
    projeto: Projeto
}

export default function SessaoEpicos({ projeto }: epicosProps) {
    const router = useRouter();
    return (
        <DropdownSection label="Épicos">
            <table className="w-full text-left">
                <thead>
                    <tr className="[&>*]:border-l-1 [&>*]:border-[#EF7541] [&>*]:py-1 [&>*]:px-2">
                        <th>Título</th>
                        <th>Criado em</th>
                        <th>Feats</th>
                        <th>PBIs</th>
                    </tr>
                </thead>

                <tbody className="[&>tr]:hover:bg-gray-900 [&>tr]:hover:cursor-pointer">
                    {projeto.epicos.map((epico) =>
                    (<tr key={epico.id} 
                    className="[&>*]:px-2 border-b border-gray-700 hover:border-gray-500"
                        onClick={() => router.push(`${projeto.id}/epicos/${epico.id}`)}>
                        <td>{epico.titulo}</td>
                        <td>{epico.createdAt}</td>
                        <td>{epico.features.length}</td>
                        <td>{epico.features.reduce(
                            (total, feature) => total + feature.pbis.length, 0
                        )}</td>
                    </tr>))}
                </tbody>
            </table>
        </DropdownSection>
    )
}