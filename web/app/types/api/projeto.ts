export type ProjetoStatus = "Rascunho" | "Inativo" | "Ativo";
export interface Projeto {
  id: number;
  titulo: string;
  descricao: string;
  status: ProjetoStatus;
  po: string;
  createdAt: string;
}