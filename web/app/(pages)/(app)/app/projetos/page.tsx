"use client";
import { projetos } from "@/app/mock/projetos";

import ProjetoCard from "@/app/components/app/projetos/ProjetoCard";


export default function projetosPage() {
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

            {/* Botão + (SVG importado e traduzido do protótipo) */}
            <button className="size-8 m-1 flex justify-center items-center hover:bg-black hover:opacity-70 hover:cursor-pointer rounded-full">
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
        </div>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projetos.length > 0 ? "" : (<p className="text-white text-md text-center col-span-full">Nenhum projeto registrado.</p>)}
            {projetos.map((projeto) => (<ProjetoCard
                key={projeto.id}
                id={projeto.id}
                projeto={projeto.titulo}
                po={projeto.po}
                createdAt={projeto.createdAt}
                status={projeto.status}
            />))}

        </section>
    </main>
    )
}