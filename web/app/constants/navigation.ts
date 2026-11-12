import { Home, MessagesSquare, FolderOpen, Users, Loader, Settings, CircleUserRound, ShieldCheck } from "lucide-react"

export const PAGINAS_PRINCIPAIS = [
  { icone: Home, label: "Página Inicial", rota: "/dashboard" },
  { icone: MessagesSquare, label: "ChatBot", rota: "/chatbot" },
  { icone: FolderOpen, label: "Projetos", rota: "/projetos" },
  { icone: Users, label: "Profissionais", rota: "/profissionais" },
  { icone: Loader, label: "Competências", rota: "/competencias" },
]

// Só aparecem no menu para quem tem is_admin
export const PAGINAS_ADMIN = [
    { icone: ShieldCheck, label: "Administração", rota: "/admin/usuarios" },
]

export const PAGINAS_CONFIG = [
    { icone: Settings, label: "Configurações", rota: "/configuracoes" },
    { icone: CircleUserRound, label: "Meu Perfil", rota: "/perfil" },
]