import { Send, Paperclip, ChevronDown, Funnel, Dot } from "lucide-react"

function ChatBot(){
    return(
        <div className="w-full h-full bg-[#010812] grid grid-rows-[10%_1fr_10%]">
            <div className="w-full h-full bg-[#010812] flex justify-between items-center px-4 sm:px-6 lg:px-8">
                <div className="w-auto h-auto flex flex-col gap-1 min-w-0">
                    <h1 className="text-white font-semibold text-lg sm:text-2xl lg:text-3xl truncate">
                        Assistente RAG Pro4Tech
                    </h1>
                    <span className="flex items-center gap-1 text-[#AEC5F4] text-xs sm:text-sm">
                        <div className="bg-green-500 w-2 h-2 rounded-[999px] shrink-0" />
                        <span className="hidden sm:inline">Contexto ativo:</span>
                    </span>
                </div>
                
                <div className="w-auto sm:w-1/3 lg:w-1/8 h-1/2 bg-[#212838] rounded-lg flex justify-center items-center gap-2 px-3 shrink-0">
                    <button type="button" className="flex items-center justify-center rounded-lg hover:bg-[#333D55] transition duration-200 p-1">
                        <ChevronDown size={20} color={"white"} />
                    </button>
                    <div className="flex flex-row gap-2 items-center">
                        <Funnel size={20} color="white" className="shrink-0" />
                        <h1 className="text-white select-none text-sm hidden md:block whitespace-nowrap">
                            Filtros de Busca
                        </h1>
                    </div>
                </div>
            </div>

            {/* chat bot aqui - vou testar com o docker  */}
            <div className="w-full h-full min-h-0 overflow-y-auto flex flex-col gap-3 px-4 sm:px-6 lg:px-8 py-4 bg-gradient-to-b from-[#010812] to-[#0C1322]"></div>

            <div className="w-full h-full bg-[#010812]">
                <div className="w-full h-full bg-[#010812] flex justify-center items-center">
                    <div className="w-full h-3/5 bg-[#010812] rounded-lg flex justify-center items-center gap-3 sm:gap-6 px-4 sm:px-6 lg:px-8">
                        <div className="relative w-6/7 h-12 sm:h-14">
                            <input
                                type="text"
                                placeholder="Pergunte sobre regras, decisões arquiteturais ou histórico de projetos..."
                                className="w-full h-full bg-[#212838] outline-none rounded-lg pl-3 sm:pl-4 pr-10 sm:pr-12 text-sm sm:text-base text-white focus:ring-2 focus:ring-[#EF7541] transition duration-200"
                            />
                            <button type="button" className="absolute right-2 sm:right-3 top-1/2 -translate-y-1/2 flex items-center justify-center cursor-pointer">
                                <Paperclip size={20} className="sm:w-6 sm:h-6" color={"#AEC5F4"} />
                            </button>
                        </div>

                        <button type="submit" className="w-12 h-12 sm:w-16 sm:h-14 bg-[#EF7541] rounded-lg flex items-center justify-center cursor-pointer hover:bg-[#d9653a] transition-colors duration-200 shrink-0">
                            <Send size={22} className="sm:w-7 sm:h-7" color={"white"} />
                        </button>

                    </div>
                </div>
            </div>
        </div>
    )
}

export default ChatBot