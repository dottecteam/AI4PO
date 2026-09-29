"use client"
import Link from "next/link"
import { LucideIcon } from "lucide-react"
import { usePathname } from "next/navigation"

interface SidebarItemProps {
  icone: LucideIcon;
  label: string;
  rota: string;
  expandido?: boolean;
}

export function SidebarItem({ icone: Icone, label, rota, expandido }: SidebarItemProps) {
  const pathname = usePathname();
  const isActive = pathname.startsWith(rota);

  return (
    <Link
      href={rota}
      className={`
        relative group flex items-center transition-all duration-200 ease-in-out
        h-10 rounded-lg mx-auto w-full
        ${expandido ? "justify-start px-3" : "w-10 justify-center"}
        ${isActive 
          ? "bg-[var(--surface-elevated)]" 
          : "bg-transparent hover:bg-[var(--surface-elevated)]/50"}
      `}
    >
      <div className="relative flex items-center justify-center">
        <Icone 
          size={18} 
          strokeWidth={isActive ? 2.5 : 2}
          className={`
            transition-all duration-200 shrink-0
            ${isActive 
              ? "text-primary" 
              : "text-[var(--foreground-muted)] group-hover:text-white"
            }
          `} 
        />
      </div>
      
      {/* Texto Lateral */}
      <span
        className={`
          overflow-hidden whitespace-nowrap text-sm transition-all duration-300 ease-in-out
          ${expandido ? "max-w-[200px] opacity-100 ml-3" : "max-w-0 opacity-0 ml-0"}
          ${isActive ? "font-semibold text-primary" : "font-medium text-[var(--foreground-muted)] group-hover:text-white"}
        `}
      >
        {label}
      </span>

      {/* Tooltip (Mostrado apenas no Desktop com a sidebar retraída) */}
      {!expandido && (
        <span className="hidden md:block absolute left-full top-1/2 -translate-y-1/2 ml-3 whitespace-nowrap bg-[var(--surface-elevated)] text-white text-xs px-2.5 py-1.5 rounded-md opacity-0 scale-95 pointer-events-none transition-all duration-200 group-hover:opacity-100 group-hover:scale-100 font-medium shadow-lg z-50 border border-gray-800">
          {label}
        </span>
      )}
    </Link>
  )
}