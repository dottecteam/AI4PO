"use client"

import Image from "next/image"
import { useState, FormEvent, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Eye, EyeOff } from "lucide-react"

const emailFormatado = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const router = useRouter()

  const [email, setEmail] = useState("")
  const [senha, setSenha] = useState("")
  const [mostrarSenha, setMostrarSenha] = useState(false)

  const [fieldErrors, setFieldErrors] = useState<{
    email?: string
    senha?: string
  }>({})

  const [apiError, setApiError] = useState("")
  const [loading, setLoading] = useState(false)

  // Captura o parâmetro da URL caso o Middleware tenha barrado o usuário
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)

    if (params.get("error") === "unauthorized") {
      setApiError("Você precisa fazer login para acessar o painel.")

      // Limpa a URL silenciosamente para a mensagem não ficar presa no F5
      window.history.replaceState(null, "", "/")
    }
  }, [])

  function validate() {
    const errors: typeof fieldErrors = {}

    if (!email) {
      errors.email = "Informe o e-mail."
    } else if (!emailFormatado.test(email)) {
      errors.email = "E-mail inválido."
    }

    if (!senha) {
      errors.senha = "Informe a senha."
    }

    setFieldErrors(errors)

    return Object.keys(errors).length === 0
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setApiError("")

    if (!validate()) return

    setLoading(true)

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/auth/login/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            senha,
          }),
        },
      )

      if (!res.ok) {
        setApiError(
          res.status === 401
            ? "E-mail ou senha incorretos."
            : "Não foi possível entrar agora. Tente novamente.",
        )

        return
      }

      router.push("/dashboard")
    } catch {
      setApiError("Falha de conexão com o servidor.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="relative flex min-h-screen w-full items-center justify-center bg-[#0C1322] bg-cover bg-center bg-no-repeat bg-fixed px-6 py-12 sm:px-16"
      style={{ backgroundImage: "url('/imageLogin.png')" }}
    >
      <div className="flex w-full max-w-5xl flex-col items-center gap-10 md:flex-row md:items-center md:justify-evenly lg:gap-16">
        {/* LOGO */}
        <div className="hidden w-full max-w-[300px] shrink-0 md:block lg:max-w-[500px]">
          <Image
            src="/imageLogo.png"
            alt="Logo AI4PO"
            width={521}
            height={521}
            className="h-auto w-full object-contain"
            priority
          />
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-8 flex flex-col items-center text-center">
            <Image
              src="/imageLogo.png"
              alt="AI4PO"
              width={56}
              height={56}
              className="mb-3 md:hidden"
            />

            <h1 className="text-2xl font-semibold text-white">AI4PO</h1>

            <p className="text-sm text-[#EF7541]">
              Gestão de Conhecimento e RAG Inteligente
            </p>
          </div>

          <form
            className="flex flex-col gap-5"
            onSubmit={handleSubmit}
            noValidate
          >
            {/* E-MAIL */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="email"
                className="text-sm font-medium text-[#EF7541]"
              >
                E-mail corporativo
              </label>

              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nome.sobrenome@empresa.com"
                className="rounded-md border border-[#F7C09A] bg-[#0C1322] px-4 py-3 text-sm text-white placeholder:text-white/40 outline-none focus:border-[#EF7541]"
              />

              {fieldErrors.email && (
                <span className="text-xs text-red-400">
                  {fieldErrors.email}
                </span>
              )}
            </div>

            {/* SENHA */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="senha"
                  className="text-sm font-medium text-[#EF7541]"
                >
                  Senha
                </label>

                <a href="#" className="text-sm text-[#EF7541] hover:underline">
                  Esqueceu a senha?
                </a>
              </div>

              <div className="relative">
                <input
                  id="senha"
                  type={mostrarSenha ? "text" : "password"}
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-md border border-[#F7C09A] bg-[#0C1322] px-4 py-3 pr-11 text-sm text-white placeholder:text-white/40 outline-none focus:border-[#EF7541]"
                />

                <button
                  type="button"
                  onClick={() => setMostrarSenha((v) => !v)}
                  aria-label={mostrarSenha ? "Ocultar senha" : "Mostrar senha"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/60 hover:text-white"
                >
                  {mostrarSenha ? <EyeOff /> : <Eye />}
                </button>
              </div>

              {fieldErrors.senha && (
                <span className="text-xs text-red-400">
                  {fieldErrors.senha}
                </span>
              )}
            </div>

            {/* ERRO DA API */}
            {apiError && (
              <p className="text-center text-sm font-medium text-red-400">
                {apiError}
              </p>
            )}

            {/* BOTÃO */}
            <button
              type="submit"
              disabled={loading}
              className="mt-2 rounded-md bg-[#EF7541] py-3 text-sm font-medium text-white transition-colors hover:bg-[#d9652f] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Entrando..." : "Entrar na Plataforma"}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-white/60">
            Acesso restrito para colaboradores da PRO4TECH.
          </p>
        </div>
      </div>
    </div>
  )
}
