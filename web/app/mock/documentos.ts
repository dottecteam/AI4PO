import { Documento } from "../types/api/documento";

export const documentosMock: Documento[] = [
  {
    id: 1,
    projetoId: 1,
    nome: "Documento de Requisitos",
    tipo: "PDF",
    data: "2026-09-01",
  },
  {
    id: 2,
    projetoId: 1,
    nome: "Plano do Projeto",
    tipo: "DOCX",
    data: "2026-09-03",
  },
  {
    id: 3,
    projetoId: 2,
    nome: "Especificação Técnica",
    tipo: "PDF",
    data: "2026-09-05",
  },
  {
    id: 4,
    projetoId: 2,
    nome: "Cronograma do Projeto",
    tipo: "XLSX",
    data: "2026-09-06",
  },
  {
    id: 5,
    projetoId: 3,
    nome: "Ata de Reunião",
    tipo: "DOCX",
    data: "2026-09-08",
  },
  {
    id: 6,
    projetoId: 3,
    nome: "Manual do Sistema",
    tipo: "PDF",
    data: "2026-09-10",
  },
  {
    id: 7,
    projetoId: 4,
    nome: "Relatório de Progresso",
    tipo: "PDF",
    data: "2026-09-12",
  },
  {
    id: 8,
    projetoId: 4,
    nome: "Levantamento de Requisitos",
    tipo: "DOCX",
    data: "2026-09-15",
  },
  {
    id: 9,
    projetoId: 5,
    nome: "Planilha de Custos",
    tipo: "XLSX",
    data: "2026-09-18",
  },
  {
    id: 10,
    projetoId: 5,
    nome: "Documentação da API",
    tipo: "PDF",
    data: "2026-09-20",
  },
];