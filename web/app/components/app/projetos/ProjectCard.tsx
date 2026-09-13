import { ProjetoStatus } from "@/app/types/api/projetos";
import Link from "next/link";

interface ProjectCardProps {
  id: string;
  project: string;
  po: string;
  date: string;
  status: ProjetoStatus;
  setor: string;
}

const statusColors: Record<ProjetoStatus, string> = {
  Rascunho: "bg-[#f4be63] text-[#9a6500]",
  Inativo: "bg-[#f6b3ad] text-[#8f3f38]",
  Ativo: "bg-[#ecfda5] text-[#526300]",
};

export default function ProjectCard({ id, project, po, date, status, setor, }: ProjectCardProps) {
  return (
    <Link href={`/app/projetos/${id}`} className="w-full rounded-xl bg-[#212838] p-5 border border-transparent
      hover:bg-[#0C1322] hover:border-white hover:cursor-pointer
    " id={id} key={id}>
      {/* Cabeçalho */}
      <div className="flex items-start justify-between">
        <p className="rounded px-2 py-1 text-xs bg-[#EF7541] text-[#212838] font-bold">
          {setor}
        </p>

        <p
          className={`rounded px-2 py-1 text-xs  font-bold ${statusColors[status]}`}
        >
          {status}
        </p>
      </div>

      {/* Nome do projeto */}
      <p className="mt-2 text-base font-semibold text-white">
        {project}
      </p>

      {/* Divisória */}
      <div className="my-4 h-px bg-[#EF7541]/60" />

      {/* Informações */}
      <div className="flex items-start justify-between">
        <p className="text-xs text-[#EF7541]">
          PO: {po}
        </p>

        <p className="text-xs text-slate-400">
          {date}
        </p>
      </div>
    </Link>
  );
}