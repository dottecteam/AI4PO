import EpicoInfo from "@/app/components/app/projetos/EpicoInfo"
import TabelaFeatures from "@/app/components/app/projetos/TabelaFeatures";
import { projetos } from "@/app/mock/projetos";
import { epicos } from "@/app/mock/epicos";

export default async function PaginaEpico({ params }: { params: Promise<{ id: number, epicoId: number }> }) {
    const { id } = await params
    const { epicoId } = await params

    const projeto = projetos.filter((proj) => proj.id == id)[0]
    const epico = epicos.filter((epic) => epic.id == epicoId)[0]


    return (
        <main className="bg-[#010812] min-h-screen px-7 pt-10 pb-20 gap-7 flex flex-col text-white">
            <EpicoInfo epico={epico} tituloProjeto={projeto.titulo}/>
            <TabelaFeatures epico={epico} projetoId={projeto.id}/>
        </main>
    )
}