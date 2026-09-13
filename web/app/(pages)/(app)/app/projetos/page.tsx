"use client";
import { projetos } from "@/app/mock/projetos";

import ProjectCard from "@/app/components/app/projetos/ProjectCard";


export default function projetosPage() {
    return (<section className="bg-[#010812] min-h-screen px-7 py-10 gap-7 flex flex-col">

        <header className="text-white">
            <h1 className=" text-2xl">Base de Conhecimentos RAG</h1>
            <p>Pesquise o histórico de todas as especificações e decisões técnicas da fábrica.</p>
        </header>

        {/* Substituir por Search Bar */}
        <div className="bg-gray-700 w-full h-15 rounded-xl flex justify-center items-center text-white text-20">
            <p>Search Bar</p>
        </div>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projetos.length > 0 ? "": (<p className="text-white text-md text-center col-span-full">Nenhum projeto registrado.</p>)}
            {projetos.map((projeto) => (<ProjectCard
                id={projeto.id}
                project={projeto.titulo}
                po={projeto.po}
                date={projeto.createdAt}
                status={projeto.status}
                setor={projeto.setor}
            />))}

        </section>
    </section>
    )
}