"use client"

import { Home, MessagesSquare, Loader, FolderOpen, CircleUserRound, Settings, ChevronsRight, ChevronsLeft } from "lucide-react"
import Link from "next/link"
import Logo from "./Logo"
import { useState } from "react"

function Sidebar() {
    const [expandido, setExpandido] = useState(false)

    const Paginas = [
        { icone: "Home", label: "Página Inicial", rota: "/" },
        { icone: "MessagesSquare", label: "ChatBot", rota: "/chatbot" },
        { icone: "FolderOpen", label: "Projetos", rota: "/projetos" },
        { icone: "Loader", label: "Competências", rota: "/competencias" }
    ]

    const Configuracoes = [
        { icone: "Settings", label: "Configurações", rota: "/configuracoes" },
        { icone: "CircleUserRound", label: "Meu Perfil", rota: "/perfil" },
    ]

    const icones = { Home, MessagesSquare, FolderOpen, Loader }
    const iconesConfig = { Settings, CircleUserRound }

    return (
        <div className={`bg-[#0C1322] h-full flex flex-col items-center justify-center gap-6 transition-all duration-300 ${expandido ? "w-80" : "w-20"}`}>

            <div className={`flex ${expandido ? "flex-row" : "flex-col"} justify-center items-center w-full`}>
                <Logo altura={60} largura={60} />
                {expandido && <h1 className="text-white text-lg font-semibold">AI4PO</h1>}
                {expandido &&
                     <button className="w-1/2 h-10 flex justify-center items-center rounded-lg hover:bg-[#212838] duration-200 px-12" onClick={() => setExpandido(!expandido)}>
                        <ChevronsLeft size={28} color={"#EF7541"} /> 
                    </button>
                }
            </div>

            {!expandido && <button className="w-1/2 h-10 flex justify-center items-center rounded-lg hover:bg-[#212838] duration-200" onClick={() => setExpandido(!expandido)}>
                <ChevronsRight size={28} color={"#EF7541"} />
            </button>}
            
            <div className="w-full h-1/4 flex flex-col items-center justify-center gap-4 p-2">
                {Paginas.map((pagina) => {
                    const Icone = icones[pagina.icone as keyof typeof icones]

                    return (
                        <Link key={pagina.rota} href={pagina.rota} className={`relative group h-20 transition-all duration-300 ${expandido ? "w-70" : "w-12"}`} >
                            <div className={`bg-[#212838] w-full h-full flex  gap-2 rounded-lg transition duration-300 hover:bg-[#010812] hover:cursor-pointer ${expandido ? "items-center justify-start pl-4" : "items-center justify-center"}`}>
                                <Icone size={28} color={"#EF7541"} />
                                {expandido && <h1 className="font-semibold text-[#AEC5F4]">{pagina.label}</h1>}
                            </div>

                            {!expandido && (
                                <span className="absolute left-full top-1/2 -translate-y-1/2 ml-2 whitespace-nowrap bg-[#212838] text-[#AEC5F4] text-sm px-2 py-1 rounded-md opacity-0 scale-95 pointer-events-none transition-all duration-200 group-hover:opacity-100 group-hover:scale-100 font-semibold select-none">
                                    {pagina.label}
                                </span>
                            )}
                        </Link>
                    )
                })}
            </div>

            {/* Parte do historico de conversas */}
            <div className="w-full h-1/2 grid-rows-[20%_auto]">
                {expandido && <div className="flex justify-center items-center"><h1 className="select-none text-sm px-2 py-1 transition-all duration-300 font-semibold text-[#EF7541]">Histórico</h1></div>}
            </div>

            <div className="w-full h-1/10 flex flex-col justify-center items-center gap-2">
                {Configuracoes.map((paginaConfig) => {
                    const IconeConfig = iconesConfig[paginaConfig.icone as keyof typeof iconesConfig]

                    return (
                        <Link key={paginaConfig.rota} href={paginaConfig.rota} className={`relative group h-20 transition-all duration-300 ${expandido ? "w-70" : "w-12"}`} >
                            <div className={`bg-[#212838] w-full h-full flex  gap-2 rounded-lg transition duration-300 hover:bg-[#010812] hover:cursor-pointer ${expandido ? "items-center justify-start pl-4" : "items-center justify-center"}`}>
                                <IconeConfig size={28} color={"#EF7541"} />
                                {expandido && <h1 className="font-semibold text-[#AEC5F4]">{paginaConfig.label}</h1>}
                            </div>

                            {!expandido && (
                                <span className="absolute left-full top-1/2 -translate-y-1/2 ml-2 whitespace-nowrap bg-[#212838] text-[#AEC5F4] text-sm px-2 py-1 rounded-md opacity-0 scale-95 pointer-events-none transition-all duration-200 group-hover:opacity-100 group-hover:scale-100 font-semibold select-none">
                                    {paginaConfig.label}
                                </span>
                            )}
                        </Link>
                    )
                })}
            </div>

        </div>
    )
}

export default Sidebar