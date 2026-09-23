"use client";

import ProjetoCard from "@/app/components/app/projetos/ProjetoCard";
import { projetoService } from "@/app/services/API/projeto/ProjetoService";
import { useEffect, useState } from "react";
import { Projeto } from "@/app/types/api/projeto";
import ProjetoCadastro from "@/app/components/app/projetos/ProjetoCadastro";
import useDebounce from "@/app/hooks/useDebounce";
import { usePesquisaEFiltro } from "@/app/hooks/usePesquisaEFiltro";
import Searchbar from "@/app/components/app/Searchbar";
import MenuFiltro from "@/app/components/app/MenuFiltro";
import DropdownSection from "@/app/components/app/projetos/DropdownSection";
import FiltroData from "@/app/components/app/FiltroData";

export default function projetosPage() {
    const [projetos, setProjetos] = useState<Projeto[]>([]);
    const [carregando, setCarregando] = useState(true);
    const [modalAberto, setModalAberto] = useState(false);

    // Pesquisa
    const [termo, setTermo] = useState("");
    const termoComDebounce = useDebounce(termo, 300);

    // Para usar nos filtros
    const statusUnicos = Array.from(new Set(projetos.map((p) => p.status)));
    const opcoesStatus: OpcaoFiltro[] = statusUnicos.map((s) => ({ rotulo: s, valor: s }));


    useEffect(() => {
        async function carregarProjetos() {
            try {
                const dados = await projetoService.listar();
                setProjetos(dados);
            } catch (erro) {
                console.error("Erro ao carregar projetos:", erro);
            } finally {
                setCarregando(false);
            }
        }
        carregarProjetos();
    }, []);

    const [filtros, setFiltros] = useState<{
        status: ValorFiltro[];
        po: ValorFiltro[];
        dataMin: string;
        dataMax: string;
    }>({
        status: [],
        po: [],
        dataMin: "",
        dataMax: "",
    });

    function atualizarFiltro(chave: string, novosSelecionados: ValorFiltro[]) {
        setFiltros((atual) => ({ ...atual, [chave]: novosSelecionados }));
    }

    function atualizarData(dataMin: string, dataMax: string) {
        setFiltros((atual) => ({ ...atual, dataMin, dataMax }));
    }

    // Para exemplo, trocar por dados reais quando conectar ao backend
    const opcoesPos: OpcaoFiltro[] = [
        { rotulo: "Ana Ferreira", valor: "Ana Ferreira" },
        { rotulo: "Bruno Costa", valor: "Bruno Costa" },
        { rotulo: "Carla Souza", valor: "Carla Souza" },
        { rotulo: "Diego Almeida", valor: "Diego Almeida" },
    ];

    const grupos: GrupoFiltro[] = [
        { chave: "status", rotulo: "Status", opcoes: opcoesStatus },
        { chave: "po", rotulo: "PO", opcoes: opcoesPos },
    ];

    const projetosFiltrados = usePesquisaEFiltro(
        projetos,
        termoComDebounce,
        (projeto, termo) => projeto.titulo.toLowerCase().includes(termo.toLowerCase()),
        filtros,
        (projeto, filtros) => {
            const dataProjeto = projeto.createdAt.slice(0, 10);

            return (
                (filtros.status.length === 0 || filtros.status.includes(projeto.status)) &&
                (filtros.po.length === 0 || filtros.po.includes(projeto.po)) &&
                (!filtros.dataMin || dataProjeto >= filtros.dataMin) &&
                (!filtros.dataMax || dataProjeto <= filtros.dataMax)
            );
        }
    );

    if (carregando) {
        return <p className="text-white text-center">Carregando...</p>;
    }

    return (<main className="bg-[#010812] min-h-screen px-7 py-10 gap-7 flex flex-col">
        <header className="text-white">
            <h1 className=" text-2xl">Base de Conhecimentos RAG</h1>
            <p>Pesquise o histórico de todas as especificações e decisões técnicas da fábrica.</p>
        </header>

        {/* Pesquisa e Filtragem */}
        <section className="w-full rounded-xl bg-[#212838] border border-transparent flex flex-even items-center gap-3 p-3">
            <Searchbar valor={termo} onAtualizar={setTermo} placeholder="Pesquise por títulos de projetos..." />
            <MenuFiltro grupos={grupos} selecionados={{ status: filtros.status, po: filtros.po }} onAtualizar={atualizarFiltro} />
            <FiltroData dataMin={filtros.dataMin} dataMax={filtros.dataMax} onAtualizar={atualizarData} />
        </section>

        {/* Título (Projetos) */}
        <div className="flex justify-between items-center border-b border-white">
            <h2 className="text-xl text-white">Projetos</h2>

            <button className="size-8 m-1 flex justify-center items-center hover:bg-black hover:opacity-70 hover:cursor-pointer rounded-full"
                onClick={() => setModalAberto(true)}>
                <svg viewBox="0 0 24 24" className="h-6 w-6 text-[#EF7541]" fill="none">
                    <path
                        d="M11.83 7.5v8.67M7.5 11.83h8.67M22.67 11.83a10.83 10.83 0 1 1-21.67 0 10.83 10.83 0 0 1 21.67 0Z"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                </svg>
            </button>

            <ProjetoCadastro aberto={modalAberto} onFechar={() => setModalAberto(false)} />
        </div>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projetosFiltrados.length > 0 ? "" : (
                <p className="text-white text-md text-center col-span-full">Nenhum projeto a exibir.</p>
            )}
            {projetosFiltrados.map((projeto) => (
                <ProjetoCard
                    key={projeto.id}
                    id={projeto.id}
                    projeto={projeto.titulo}
                    po={projeto.po}
                    createdAt={projeto.createdAt}
                    status={projeto.status}
                />
            ))}
        </section>
    </main>
    )
}