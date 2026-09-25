import { Home, MessagesSquare, FolderOpen, Loader, Settings, CircleUserRound } from "lucide-react"

export const PAGINAS_PRINCIPAIS = [
    { icone: Home, label: "Página Inicial", rota: "/dashboard" },
    { icone: MessagesSquare, label: "ChatBot", rota: "/chatbot" },
    { icone: FolderOpen, label: "Projetos", rota: "/projetos" },
    { icone: Loader, label: "Competências", rota: "/competencias" },
]

export const PAGINAS_CONFIG = [
    { icone: Settings, label: "Configurações", rota: "/configuracoes" },
    { icone: CircleUserRound, label: "Meu Perfil", rota: "/perfil" },
]