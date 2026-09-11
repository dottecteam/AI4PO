import { Send, Paperclip } from "lucide-react"

function ChatBot(){
    return(
        <div className="w-full h-full bg-[#010812] grid grid-rows-[10%_auto_10%]">
            <div className="w-full h-full bg-[#010812]"></div>

            <div className="w-full h-full bg-gradient-to-b from-[#010812] to-[#0C1322]"></div>

            <div className="w-full h-full bg-[#010812]">
                <div className="w-full h-full bg-[#010812] flex justify-center items-center">
                    <div className="w-full h-3/5 bg-[#010812] rounded-lg flex justify-center items-center gap-6">
                        <div className="relative w-6/7 h-14">
                            <input type="text" className="w-full h-full bg-[#212838] outline-none rounded-lg pl-4 pr-12 text-white focus:ring-2 focus:ring-[#EF7541] transition duration-200" />
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