'use client';

import DropdownSection from "@/app/components/app/projetos/DropdownSection";
import { features } from "@/app/mock/features";
import { pbis } from "@/app/mock/pbis";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Epico } from "@/app/types/api/epico";
import { epicosService } from "@/app/services/API/projeto/EpicoService";
import { useProjetoAtual } from "@/app/contexts/ProjetoContext";


export default function TabelaEpicos() {
    const projeto = useProjetoAtual()
    if (!projeto) return <p className="text-white text-center">Projeto não encontrado.</p>;

    const [epicos, setEpicos] = useState<Epico[]>([])
    const [carregando, setCarregando] = useState(true)
    const router = useRouter();

    useEffect(() => {
        async function carregarEpicos() {
            if (!projeto) return;
            try {
                const dados = await epicosService.listarPorProjeto(projeto.id);
                setEpicos(dados);
            } catch (erro) {
                console.error("Erro ao carregar epicos:", erro);
            } finally {
                setCarregando(false);
            }
        }
        carregarEpicos();
    }, []);

    if (carregando) {
        return <p className="text-white text-center">Carregando...</p>;
    }

    return (
        <DropdownSection label="Épicos">
            {/* Verifica se há épicos e cria a tabela */}
            {epicos.length > 0 ?
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
                        {epicos.map((epico) =>
                        (<tr key={epico.id}
                            className="[&>*]:px-2 border-b border-gray-700 hover:border-gray-500"
                            onClick={() => {
                                if (!projeto || !epico ) return
                                router.push(`/app/projetos/${projeto.id}/epicos/${epico.id}`)
                            }}>
                            <td>{epico.titulo}</td>
                            <td>{new Date(epico.createdAt).toLocaleDateString('pt-BR')}</td>
                            <td>{features.filter((feat) => feat.idEpico == epico.id).length}</td>
                            <td>{pbis.filter((pbi) => pbi.idFeature in features.filter((feat) => feat.idEpico == epico.id)).length
                            }</td>
                        </tr>))}
                    </tbody>
                </table>) : (
                    <p className="px-3 text-sm text-gray-500">Nenhum épico registrado.</p>
                )
            }

        </DropdownSection>
    )
}