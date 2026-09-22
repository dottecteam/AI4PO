export interface Feature {
  id: number;
  idEpico: number;
  titulo: string;
  descricao: string;
  objetivo: string;
  criteriosAceitacao: string[];
  createdAt: string;
}

export interface FeatureInput{
  idEpico: number;
  titulo: string;
  descricao: string;
  objetivo: string;
  criteriosAceitacao: string[];
}