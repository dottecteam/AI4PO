'use client';

import DropdownSection from "@/app/components/app/projetos/DropdownSection";
import { Epico } from "@/app/types/api/epico";
import { pbis } from "@/app/mock/pbis";
import { useRouter } from "next/navigation";
import { featureService } from "@/app/services/API/projeto/FeatureService";
import { useEffect, useState } from "react";
import { Feature } from "@/app/types/api/feature";
import { useEpicoAtual } from "@/app/contexts/EpicoContext";
import { useProjetoAtual } from "@/app/contexts/ProjetoContext";
import FeatureCadastro from "./FeatureCadastro";

export default function TabelaFeatures() {
    const epico = useEpicoAtual()
    const projeto = useProjetoAtual()
    if (!epico || !projeto) return <p className="text-white text-center">Erro ao ler dados.</p>;

    const [features, setFeatures] = useState<Feature[]>([])
    const [carregando, setCarregando] = useState(true)
    const router = useRouter();

    const [modalAberto, setModalAberto] = useState(false)

    useEffect(() => {
        async function carregarEpicos() {
            if (!epico) return;
            try {
                const dados = await featureService.listarPorEpico(epico.id);
                setFeatures(dados);
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
        <DropdownSection label="Features" onAdd={() => setModalAberto(true)}>
            <FeatureCadastro aberto={modalAberto} onFechar={() => setModalAberto(false)} />
            {/* Verifica se há features e cria a tabela */}
            {features.length > 0 ?
                (<table className="w-full text-left">
                    <thead>
                        <tr className="[&>*]:border-l-1 [&>*]:border-[#EF7541] [&>*]:py-1 [&>*]:px-2">
                            <th>Título</th>
                            <th>Criado em</th>
                            <th>PBIs</th>
                        </tr>
                    </thead>

                    <tbody className="[&>tr]:hover:bg-gray-900 [&>tr]:hover:cursor-pointer">
                        {features.map((feat) =>
                        (<tr key={feat.id}
                            className="[&>*]:px-2 border-b border-gray-700 hover:border-gray-500"
                            onClick={() => {
                                if (!projeto || !epico) return;
                                router.push(`/app/projetos/${projeto.id}/epicos/${epico.id}/features/${feat.id}/`)
                            }}>
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