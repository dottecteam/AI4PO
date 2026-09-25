export default function AuthLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <div className="w-full h-screen bg-background flex">
            <main className="flex-1 overflow-y-auto">
                {children}
            </main>
        </div>
    )
}