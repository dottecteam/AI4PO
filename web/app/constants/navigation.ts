import {
  Home,
  MessagesSquare,
  FolderOpen,
  Loader,
  CircleUserRound,
  ShieldCheck,
  Network,
  Users,
} from "lucide-react"

export const PAGINAS_PRINCIPAIS = [
  { icone: Home, label: "Página Inicial", rota: "/dashboard" },
  { icone: MessagesSquare, label: "Novo Chat", rota: "/chatbot" },
  { icone: FolderOpen, label: "Projetos", rota: "/projetos" },
  { icone: Network, label: "Grafo Global", rota: "/grafo" },
  { icone: Users, label: "Profissionais", rota: "/profissionais" },
  { icone: Loader, label: "Competências", rota: "/competencias" },
]

export const PAGINAS_CONFIG = [
  { icone: CircleUserRound, label: "Meu Perfil", rota: "/perfil" },
]

// Só aparecem no menu para quem tem is_admin
export const PAGINAS_ADMIN = [
  { icone: ShieldCheck, label: "Administração", rota: "/admin/usuarios" },
]
