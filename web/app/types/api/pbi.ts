export interface PBI {
  id: number;
  idFeature: number;
  titulo: string;
  userStory: {
    como: string;
    quero: string;
    paraQue: string;
  };
  regras?: string;
  cenarios: {
    dado: string;
    quando: string;
    entao: string;
  }[]
  createdAt: string;
}

export interface PBIInput {
  idFeature: number;
  titulo: string;
  userStory: {
    como: string;
    quero: string;
    paraQue: string;
  };
  regras?: string;
  cenarios: {
    dado: string;
    quando: string;
    entao: string;
  }[]
}