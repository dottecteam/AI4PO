'use client';

import DropdownSection from "@/app/components/app/projetos/DropdownSection";
import { Projeto } from "@/app/types/api/projeto";
import { epicos } from "@/app/mock/epicos";
import { features } from "@/app/mock/features";
import { pbis } from "@/app/mock/pbis";
import { useRouter } from "next/navigation";

interface epicosProps {
    projeto: Projeto
}

export default function TabelaEpicos({ projeto }: epicosProps) {
    const router = useRouter();
    const epicos_filtrados = epicos.filter((epico_) => epico_.idProjeto == projeto.id)


    return (
        <DropdownSection label="Épicos">
            {/* Verifica se há épicos e cria a tabela */}
            {epicos_filtrados.length > 0 ?
                (<table className="w-full text-left">
                    <thead>
                        <tr className="[&>*]:border-l-1 [&>*]:border-[#EF7541] [&>*]:py-1 [&>*]:px-2">
                            <th>Título</th>
                            <th>Criado em</th>
                            <th>Feats</th>
                            <th>PBIs</th>
                        </tr>
                    </thead>

                    <tbody className="[&>tr]:hover:bg-gray-900 [&>tr]:hover:cursor-pointer">
                        {epicos_filtrados.map((epico) =>
                        (<tr key={epico.id}
                            className="[&>*]:px-2 border-b border-gray-700 hover:border-gray-500"
                            onClick={() => router.push(`/app/projetos/${projeto.id}/epicos/${epico.id}`)}>
                            <td>{epico.titulo}</td>
                            <td>{new Date(epico.createdAt).toLocaleDateString('pt-BR')}</td>
                            <td>{features.filter((feat) => feat.idEpico == epico.id).length}</td>
                            <td>{pbis.filter((pbi) => pbi.idFeature in features.filter((feat) => feat.idEpico == epico.id)).length
                            }</td>
                        </tr>))}
                    </tbody>
                </table>) : (
                    <p  className="px-3 text-sm text-gray-500">Nenhum épico registrado.</p>
                )
            }

        </DropdownSection>
    )
}