import { Documento } from "../types/api/documento";

export const documentosMock: Documento[] = [
  {
    id: 1,
    projetoId: 1,
    nome: "Documento de Requisitos",
    tipo: "PDF",
    data: "2026-09-01T09:15:22.000000-03:00",
  },
  {
    id: 2,
    projetoId: 1,
    nome: "Plano do Projeto",
    tipo: "DOCX",
    data: "2026-09-03T14:32:10.000000-03:00",
  },
  {
    id: 3,
    projetoId: 2,
    nome: "Especificação Técnica",
    tipo: "PDF",
    data: "2026-09-05T11:05:47.000000-03:00",
  },
  {
    id: 4,
    projetoId: 2,
    nome: "Cronograma do Projeto",
    tipo: "XLSX",
    data: "2026-09-06T16:48:03.000000-03:00",
  },
  {
    id: 5,
    projetoId: 3,
    nome: "Ata de Reunião",
    tipo: "DOCX",
    data: "2026-09-08T08:20:59.000000-03:00",
  },
  {
    id: 6,
    projetoId: 3,
    nome: "Manual do Sistema",
    tipo: "PDF",
    data: "2026-09-10T13:41:36.000000-03:00",
  },
  {
    id: 7,
    projetoId: 4,
    nome: "Relatório de Progresso",
    tipo: "PDF",
    data: "2026-09-12T10:12:18.000000-03:00",
  },
  {
    id: 8,
    projetoId: 4,
    nome: "Levantamento de Requisitos",
    tipo: "DOCX",
    data: "2026-09-15T17:55:41.000000-03:00",
  },
  {
    id: 9,
    projetoId: 5,
    nome: "Planilha de Custos",
    tipo: "XLSX",
    data: "2026-09-18T09:38:27.000000-03:00",
  },
  {
    id: 10,
    projetoId: 5,
    nome: "Documentação da API",
    tipo: "PDF",
    data: "2026-09-20T22:07:55.788856-03:00",
  },
];