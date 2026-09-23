'use client';

import DropdownSection from "@/app/components/app/projetos/DropdownSection";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { pbiService } from "@/app/services/API/projeto/PBIService";
import { PBI } from "@/app/types/api/pbi";
import { useProjetoAtual } from "@/app/contexts/ProjetoContext";
import { useEpicoAtual } from "@/app/contexts/EpicoContext";
import { useFeatureAtual } from "@/app/contexts/FeatureContext";
import PbiCadastro from "./PbiCadastro";
import Searchbar from "@/app/components/app/Searchbar";


export default function TabelaPbis() {
    const projeto = useProjetoAtual()
    const epico = useEpicoAtual()
    const feature = useFeatureAtual()

    const [pbis, setPbis] = useState<PBI[]>([])
    const [carregando, setCarregando] = useState(true)
    const [termo, setTermo] = useState("")
    const [modalAberto, setModalAberto] = useState(false)
    const router = useRouter();

    useEffect(() => {
        async function carregarPbis() {
            if (!feature) return;
            try {
                const dados = await pbiService.listarPorFeature(feature.id);
                setPbis(dados);
            } catch (erro) {
                console.error("Erro ao carregar pbis:", erro);
            } finally {
                setCarregando(false);
            }
        }
        carregarPbis();
    }, [feature]);

    if (!projeto || !epico || !feature) return <p className="text-white text-center">Erro ao ler dados.</p>;
    if (carregando) return <p className="text-white text-center">Carregando...</p>;

    const pbisFiltrados = pbis.filter((pbi) =>
        pbi.titulo.toLowerCase().includes(termo.toLowerCase())
    );

    return (
        <DropdownSection label="PBIs" onAdd={() => setModalAberto(true)}>
            <PbiCadastro aberto={modalAberto} onFechar={() => setModalAberto(false)} />

            <Searchbar valor={termo} onAtualizar={setTermo} placeholder="Pesquise por um PBI..."
                className="flex items-center w-full bg-gray-900 m-2 text-sm py-2 focus:bg-gray-800 h-6 rounded-md"
                estiloInput="w-full mx-3 px-3 text-gray-200 outline-none" />

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
                        onClick={() => {
                            router.push(`/app/projetos/${projeto.id}/epicos/${epico.id}/features/${feature.id}/pbis/${pbi.id}`);
                        }}>
                        <td>{pbi.titulo}</td>
                        <td>{new Date(pbi.createdAt).toLocaleDateString('pt-BR')}</td>
                    </tr>))}
                </tbody>
            </table>) : (
                <p className="px-3 text-sm text-gray-500">Nenhum Product Backlog Item a exibir.</p>
            )}
        </DropdownSection>
    )
}