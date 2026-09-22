'use client';

import DropdownSection from "@/app/components/app/projetos/DropdownSection";
import { Feature } from "@/app/types/api/feature";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { pbiService } from "@/app/services/API/projeto/PBIService";
import { PBI } from "@/app/types/api/pbi";
import { useProjetoAtual } from "@/app/contexts/ProjetoContext";
import { useEpicoAtual } from "@/app/contexts/EpicoContext";
import { useFeatureAtual } from "@/app/contexts/FeatureContext";
import { usePbiAtual, useSetPbicoAtual } from "@/app/contexts/PbiContext";


export default function TabelaPbis() {
    const projeto = useProjetoAtual()
    const epico = useEpicoAtual()
    const feature = useFeatureAtual()
    if (!projeto || !epico || !feature) return <p className="text-white text-center">Erro ao ler dados.</p>;

    const [pbis, setPbis] = useState<PBI[]>([])
    const [carregando, setCarregando] = useState(true)
    const router = useRouter();

    useEffect(() => {
        async function carregarEpicos() {
            if (!feature) return;
            try {
                const dados = await pbiService.listarPorFeature(feature.id);
                setPbis(dados);
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
        <DropdownSection label="PBIs">
            {pbis.length > 0 ? (<table className="w-full text-left">
                <thead>
                    <tr className="[&>*]:border-l-1 [&>*]:border-[#EF7541] [&>*]:py-1 [&>*]:px-2">
                        <th>Título</th>
                        <th>Criado em</th>
                    </tr>
                </thead>

                <tbody className="[&>tr]:hover:bg-gray-900 [&>tr]:hover:cursor-pointer">
                    {pbis.map((pbi) =>
                    (<tr key={pbi.id}
                        className="[&>*]:px-2 border-b border-gray-700 hover:border-gray-500"
                        onClick={() => {
                            if (!projeto || !epico || !feature) return;
                            router.push(`/app/projetos/${projeto.id}/epicos/${epico.id}/features/${feature.id}/pbis/${pbi.id}`);
                        }}>
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