"use client"

import { createContext, useContext, useEffect, useState } from "react"
import { buscarUsuarioLogado, encerrarSessao, sessaoInvalida} from "@/app/services/API/usuarios"
import type { UsuarioLogado } from "@/app/types/api/usuario"

type AuthState = {
  usuario: UsuarioLogado | null
  carregando: boolean
}

const AuthContext = createContext<AuthState>({ usuario: null, carregando: true })

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [estado, setEstado] = useState<AuthState>({ usuario: null, carregando: true })

  useEffect(() => {
    let ativo = true

    buscarUsuarioLogado()
      .then((usuario) => {
        if (ativo) setEstado({ usuario, carregando: false })
      })
      .catch((erro) => {
        if (sessaoInvalida(erro)) {
          encerrarSessao()
          return
        }
        
        if (ativo) setEstado({ usuario: null, carregando: false })
      })

    return () => {
      ativo = false
    }
  }, [])

  if (estado.carregando) {
    return <div className="w-full h-screen bg-background" aria-busy="true" />
  }

  return <AuthContext.Provider value={estado}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}