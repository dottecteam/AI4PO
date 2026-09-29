"use client";

import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { projetoService } from "@/app/services/API/projeto/ProjetoService";
import { Projeto } from "@/app/types/api/projeto";
import ProjetoCard from "@/app/components/app/projetos/ProjetoCard";
import ProjetoCadastro from "@/app/components/app/projetos/ProjetoCadastro";
import Searchbar from "@/app/components/app/Searchbar";
import MenuFiltro from "@/app/components/app/MenuFiltro";
import FiltroData from "@/app/components/app/FiltroData";
import useDebounce from "@/app/hooks/useDebounce";
import { usePesquisaEFiltro } from "@/app/hooks/usePesquisaEFiltro";

export default function Projetos() {
    const [projetos, setProjetos] = useState<Projeto[]>([]);
    const [carregando, setCarregando] = useState(true);
    const [modalAberto, setModalAberto] = useState(false);

    // Pesquisa
    const [termo, setTermo] = useState("");
    const termoComDebounce = useDebounce(termo, 300);

    // Filtros
    const [filtros, setFiltros] = useState<{
        status: string[];
        po: string[];
        dataMin: string;
        dataMax: string;
    }>({
        status: [],
        po: [],
        dataMin: "",
        dataMax: "",
    });

    const statusUnicos = ["Ativo", "Rascunho", "Inativo"];
    const opcoesStatus = statusUnicos.map((s) => ({ rotulo: s, valor: s }));

    // Mock do filtro
    const opcoesPos = [
        { rotulo: "Ana Ferreira", valor: "Ana Ferreira" },
        { rotulo: "Bruno Costa", valor: "Bruno Costa" },
        { rotulo: "Carla Souza", valor: "Carla Souza" },
        { rotulo: "Diego Almeida", valor: "Diego Almeida" },
    ];

    const grupos = [
        { chave: "status", rotulo: "Status", opcoes: opcoesStatus },
        { chave: "po", rotulo: "PO", opcoes: opcoesPos },
    ];

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

    function atualizarFiltro(chave: string, novosSelecionados: (string | number)[]) {
        setFiltros((atual) => ({ ...atual, [chave]: novosSelecionados as string[] }));
    }

    function atualizarData(dataMin: string, dataMax: string) {
        setFiltros((atual) => ({ ...atual, dataMin, dataMax }));
    }

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
        return (
            <div className="flex h-full items-center justify-center min-h-screen bg-[var(--background)]">
                <p className="text-[var(--foreground-muted)] text-sm animate-pulse">Carregando...</p>
            </div>
        );
    }

    return (
        <main className="bg-background min-h-screen px-7 py-10 gap-7 flex flex-col">
            
            <header className="text-white flex flex-col gap-1">
                <h1 className="text-2xl font-bold">Base de Conhecimentos RAG</h1>
                <p className="text-[var(--foreground-muted)]">
                    Pesquise o histórico de todas as especificações e decisões técnicas da fábrica.
                </p>
            </header>

            {/* Pesquisa e Filtragem (Classes originais preservadas) */}
            <section className="w-full rounded-xl bg-[var(--surface-elevated)] border border-transparent flex flex-even items-center gap-3 p-3">
                <Searchbar 
                    valor={termo} 
                    onAtualizar={setTermo} 
                    placeholder="Pesquise por títulos de projetos..." 
                />
                <MenuFiltro 
                    grupos={grupos} 
                    selecionados={{ status: filtros.status, po: filtros.po }} 
                    onAtualizar={atualizarFiltro} 
                />
                <FiltroData 
                    dataMin={filtros.dataMin} 
                    dataMax={filtros.dataMax} 
                    onAtualizar={atualizarData} 
                />
            </section>

            {/* Projetos */}
            <section className="flex flex-col gap-4">
                <div className="flex justify-between items-center border-b border-white pb-2">
                    <h2 className="text-xl text-white">Projetos</h2>
                    
                    {/* Botão Organizado com Lucide Icon */}
                    <button 
                        className="flex size-8 items-center justify-center rounded-full text-primary hover:bg-black hover:opacity-70 transition-all cursor-pointer"
                        onClick={() => setModalAberto(true)}
                        title="Cadastrar Novo Projeto"
                    >
                        <Plus size={24} strokeWidth={2.5} />
                    </button>
                    
                    <ProjetoCadastro aberto={modalAberto} onFechar={() => setModalAberto(false)} />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                    {projetosFiltrados.length > 0 ? (
                        projetosFiltrados.map((projeto) => (
                            <ProjetoCard
                                key={projeto.id}
                                id={projeto.id}
                                projeto={projeto.titulo}
                                po={projeto.po}
                                createdAt={projeto.createdAt}
                                status={projeto.status}
                            />
                        ))
                    ) : (
                        <p className="text-white text-md text-center col-span-full py-6">
                            Nenhum projeto a exibir.
                        </p>
                    )}
                </div>
            </section>
        </main>
    );
}