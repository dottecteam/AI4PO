"use client";

import ProjetoCard from "@/app/components/app/projetos/ProjetoCard";
import { projetoService } from "@/app/services/API/projeto/ProjetoService";
import { useEffect, useState } from "react";
import { Projeto } from "@/app/types/api/projeto";
import ProjetoCadastro from "@/app/components/app/projetos/ProjetoCadastro";


export default function projetosPage() {
    const [projetos, setProjetos] = useState<Projeto[]>([]);
    const [carregando, setCarregando] = useState(true);
    const [modalAberto, setModalAberto] = useState(false);

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

    if (carregando) {
        return <p className="text-white text-center">Carregando...</p>;
    }

    return (<main className="bg-[#010812] min-h-screen px-7 py-10 gap-7 flex flex-col">
        <header className="text-white">
            <h1 className=" text-2xl">Base de Conhecimentos RAG</h1>
            <p>Pesquise o histórico de todas as especificações e decisões técnicas da fábrica.</p>
        </header>

        {/* Substituir por Search Bar */}
        <div className="bg-gray-700 w-full h-15 rounded-xl flex justify-center items-center text-white text-20">
            <p>Search Bar</p>
        </div>

        {/* Título (Projetos) */}
        <div className="flex justify-between items-center border-b border-white">
            <h2 className="text-xl text-white">Projetos</h2>

            {/* Botão cadastro (SVG importado e traduzido do protótipo) */}
            <button className="size-8 m-1 flex justify-center items-center hover:bg-black hover:opacity-70 hover:cursor-pointer rounded-full"
            onClick={() => setModalAberto(true)}>
                <svg
                    viewBox="0 0 24 24"
                    className="h-6 w-6 text-[#EF7541]"
                    fill="none"
                >
                    <path
                        d="M11.83 7.5v8.67M7.5 11.83h8.67M22.67 11.83a10.83 10.83 0 1 1-21.67 0 10.83 10.83 0 0 1 21.67 0Z"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                </svg>
            </button>

            <ProjetoCadastro aberto={modalAberto} onFechar={() => setModalAberto(false)}/>
        </div>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projetos.length > 0 ? "" : (<p className="text-white text-md text-center col-span-full">Nenhum projeto registrado.</p>)}
            {projetos.map((projeto) => (
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