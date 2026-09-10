import { Home, MessagesSquare, Loader, FolderOpen, CircleUserRound, Settings } from "lucide-react"
import Link from "next/link"
import Logo from "./Logo"

function Sidebar() {

    const Paginas = [
        { icone: "Home", label: "Página Inicial", rota: "/" },
        { icone: "MessagesSquare", label: "Chat", rota: "/chatbot" },
        { icone: "FolderOpen", label: "Projetos", rota: "/projetos" },
        { icone: "Loader", label: "Competências", rota: "/competencias" }
    ]

    const Configuracoes = [
        { icone: "Settings", label: "Configurações", rota: "/configuracoes" },
        { icone: "CircleUserRound", label: "Meu Perfil", rota: "/perfil" },
    ]

    const icones = {
        Home,
        MessagesSquare,
        FolderOpen,
        Loader
    }

    const iconesConfig = {
        Settings,
        CircleUserRound
    }

    return (
        <div className="bg-[#0C1322] h-full w-20 flex flex-col items-center justify-center gap-6">

            <Logo altura={60} largura={60} />

            <div className="w-full h-1/4 flex flex-col items-center justify-center gap-4 p-2">
                {Paginas.map((pagina) => {
                    const Icone = icones[pagina.icone as keyof typeof icones]

                    return (
                        <Link key={pagina.rota} href={pagina.rota} className="relative group w-12 h-20">
                            <div className="bg-[#212838] w-full h-full flex items-center justify-center rounded-lg transition duration-300 hover:bg-[#010812] hover:cursor-pointer">
                                <Icone size={28} color={"#EF7541"} />
                            </div>

                            <span className="absolute left-full top-1/2 -translate-y-1/2 ml-2 whitespace-nowrap bg-[#212838] text-white text-sm px-2 py-1 rounded-md opacity-0 scale-95 pointer-events-none transition-all duration-200 group-hover:opacity-100 group-hover:scale-100 font-semibold select-none">
                                {pagina.label}
                            </span>
                        </Link>
                    )
                })}
            </div>

            
            {/* Parte do historico de conversas */}
            <div className="w-full h-1/2" />

            <div className="w-full h-1/10 flex flex-col justify-center items-center gap-2">
                {Configuracoes.map((paginaConfig) => {
                    const IconeConfig = iconesConfig[paginaConfig.icone as keyof typeof iconesConfig]

                    return (
                        <Link key={paginaConfig.rota} href={paginaConfig.rota} className="relative group w-12 h-20">
                            <div className="bg-[#212838] w-full h-full flex items-center justify-center rounded-lg transition duration-300 hover:bg-[#010812] hover:cursor-pointer">
                                <IconeConfig size={28} color={"#EF7541"} />
                            </div>

                            <span className="absolute left-full top-1/2 -translate-y-1/2 ml-2 whitespace-nowrap bg-[#212838] text-white text-sm px-2 py-1 rounded-md opacity-0 scale-95 pointer-events-none transition-all duration-200 group-hover:opacity-100 group-hover:scale-100 font-semibold select-none">
                                {paginaConfig.label}
                            </span>
                        </Link>
                    )
                })}
            </div>

        </div>
    )
}

export default Sidebar