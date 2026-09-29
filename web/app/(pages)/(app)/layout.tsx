import Sidebar from "../../components/Sidebar"

export default function AppLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <div className="w-full h-screen bg-background flex overflow-hidden relative">
            <Sidebar />
            
            <div className="md:hidden fixed top-0 left-0 w-full h-32 bg-gradient-to-b from-background via-background/80 to-transparent z-30 pointer-events-none" />

            <main className="flex-1 overflow-y-auto pt-15 md:pt-0 flex flex-col">
                <div className="w-full max-w-screen-2xl mx-auto h-full flex flex-col flex-1">
                    {children}
                </div>
            </main>
        </div>
    )
}