export interface Feature {
  id: number;
  idEpico: number;
  titulo: string;
  descricao: string;
  objetivo: string;
  criteriosAceitacao: string[];
  createdAt: string;
  totalPbis: number;
}

export interface FeatureInput{
  idEpico: number;
  titulo: string;
  descricao: string;
  objetivo: string;
  criteriosAceitacao: string[];
}