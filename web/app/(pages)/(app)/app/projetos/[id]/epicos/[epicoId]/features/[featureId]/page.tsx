import FeatureInfo from "@/app/components/app/projetos/FeatureInfo";
import TabelaPbis from "@/app/components/app/projetos/TabelaPbis";
import { projetos } from "@/app/mock/projetos";
import { epicos } from "@/app/mock/epicos";
import { features } from "@/app/mock/features";

export default async function PaginaFeature({ params }: { params: Promise<{ id: number, epicoId: number, featureId: number }> }) {
    const { id, epicoId, featureId } = await params

    const projeto = projetos.filter((proj) => proj.id == id)[0]
    const epico = epicos.filter((epic) => epic.id == epicoId)[0]
    const feature = features.filter((feat) => feat.id == featureId)[0]

    if (!feature) {
        return;
    }

    return (
        <main className="bg-[#010812] min-h-screen px-7 pt-10 pb-20 gap-7 flex flex-col text-white">
            <FeatureInfo feature={feature} tituloEpico={epico.titulo}/>
            <TabelaPbis feature={feature} epicoId={epico.id} projetoId={projeto.id}/>
        </main>
    )
}