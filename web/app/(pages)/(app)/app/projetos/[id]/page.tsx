import ProjetoInfo from "@/app/components/app/projetos/ProjetoInfo";
import SessaoEpicos from "@/app/components/app/projetos/SessaoEpicos";
import { projetos } from "@/app/mock/projetos";

export default async function PaginaProjeto({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params
    const projeto = projetos.filter((proj) => proj.id == id)[0]


    function handleAdd() {
        console.log("adicionar");
    }


    return (
        <main className="bg-[#010812] min-h-screen px-7 pt-10 pb-20 gap-7 flex flex-col text-white">

            <ProjetoInfo projeto={projeto}/>
            <SessaoEpicos projeto={projeto}/>


        </main>
    );
}