import Breadcrumb from "@/app/components/app/projetos/Breadcrumb";
import PBIInfo from "@/app/components/app/projetos/PbiInfo";
import { features } from "@/app/mock/features";
import { pbis } from "@/app/mock/pbis";

export default async function PaginaFeature({ params }: { params: Promise<{ featureId: number, pbiId: number }> }) {
    const { featureId, pbiId } = await params

    const feature = features.filter((feat) => feat.id == featureId)[0]
    const pbi = pbis.filter((pbi_) => pbi_.id == pbiId)[0]

    return (
        <main className="bg-[#010812] min-h-screen px-7 pt-10 pb-20 gap-5 flex flex-col text-white">
            <Breadcrumb />
            <PBIInfo />
        </main>
    )
}