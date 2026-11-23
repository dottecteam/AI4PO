export type EstadoDocumento = "pendente" | "processando" | "processado" | "erro"

export interface Documento {
  id: number
  projeto: number
  nome: string
  tipo: string
  data: string
  estado: EstadoDocumento
  mensagemErro?: string
}
