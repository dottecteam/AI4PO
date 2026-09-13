export type ProjetoStatus = "Rascunho" | "Inativo" | "Ativo";

export interface Cenario {
  id: string;
  titulo: string;
  dado: string;
  quando: string;
  entao: string;
}

export interface PBI {
  id: string;
  titulo: string;
  userStory: {
    como: string;
    quero: string;
    paraQue: string;
  };
  prototipo?: string;
  cenarios: Cenario[];
  regras?: string[];
}

export interface Feature {
  id: string;
  titulo: string;
  descricao: string;
  objetivo: string;
  criterioDeAceitacao: string[];
  pbis: PBI[];
}

export interface Epico {
  id: string;
  titulo: string;
  descricao: string;
  objetivo: string;
  escopoMacro: string[];
  resultadoEsperado: string;
  criterioDeAceitacao: string[];
  features: Feature[];
}

export interface Projeto {
  id: string;
  titulo: string;
  setor: string;
  status: ProjetoStatus;
  po: string;
  createdAt: string;
  epicos: Epico[];
}