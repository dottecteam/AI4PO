import { Send, Paperclip, ChevronDown, Funnel, Dot } from "lucide-react"

function ChatBot(){
    return(
        <div className="w-full h-full bg-[#010812] grid grid-rows-[10%_1fr_10%]">
            <div className="w-full h-full bg-[#010812] flex justify-between items-center px-8">
                <div className="w-auto h-auto flex flex-col gap-1">
                    <h1 className="text-white font-semibold text-3xl">Assistente RAG Pro4Tech</h1>
                    <span className="flex items-center gap-1 text-[#AEC5F4]">
                        <div className="bg-green-500 w-2 h-2 rounded-[999px]" />
                        Contexto ativo:
                    </span>
                </div>
                
                <div className="w-1/8 h-1/2 bg-[#212838] rounded-lg flex justify-center items-center">
                    <button type="button" className="w-1/6 h-1/2 flex justify-center items-center rounded-lg hover:bg-[#333D55] transition duration-200">
                        <ChevronDown size={20} color={"white"} />
                    </button>
                    <div className="flex flex-row gap-2 items-center">
                        <Funnel size={24} color="white" />
                        <h1 className="text-white select-none">Filtros de Busca</h1>
                    </div>
                </div>
            </div>

            {/* chat bot aqui - vou testar com o docker  */}
            <div className="w-full h-full min-h-0 overflow-y-auto flex flex-col gap-3 px-8 py-4 bg-gradient-to-b from-[#010812] to-[#0C1322]"></div>

            <div className="w-full h-full bg-[#010812]">
                <div className="w-full h-full bg-[#010812] flex justify-center items-center">
                    <div className="w-full h-3/5 bg-[#010812] rounded-lg flex justify-center items-center gap-6">
                        <div className="relative w-6/7 h-14">
                            <input type="text" placeholder="Pergunte sobre regras, decisões arquiteturais ou histórico de projetos..." className="w-full h-full bg-[#212838] outline-none rounded-lg pl-4 pr-12 text-white focus:ring-2 focus:ring-[#EF7541] transition duration-200" />
                            <button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center justify-center cursor-pointer">
                                <Paperclip size={24} color={"#AEC5F4"} />
                            </button>
                        </div>

                        <button type="submit" className="w-16 h-14 bg-[#EF7541] rounded-lg flex items-center justify-center cursor-pointer hover:bg-[#d9653a] transition-colors duration-200">
                            <Send size={28} color={"white"} />
                        </button>

                    </div>
                </div>
            </div>
        </div>
    )
}

export default ChatBot