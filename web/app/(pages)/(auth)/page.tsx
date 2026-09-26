"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { validarEmail, validarSenha } from "@/app/utils/validators"
import { Input } from "@/app/components/ui/Input"
import { Button } from "@/app/components/ui/Button"
import { BrandLogo } from "@/app/components/ui/BrandLogo" // Importando o novo componente

export default function Login() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [senha, setSenha] = useState("")
  const [fieldErrors, setFieldErrors] = useState<{
    email?: string
    senha?: string
  }>({})
  const [apiError, setApiError] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get("error") === "unauthorized") {
      setApiError("Você precisa fazer login para acessar o painel.")
      window.history.replaceState(null, "", "/")
    }
  }, [])

  function validate() {
    const erroEmail = validarEmail(email)
    const erroSenha = validarSenha(senha)

    setFieldErrors({ email: erroEmail, senha: erroSenha })
    return !erroEmail && !erroSenha
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
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
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, senha }),
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
      className="relative flex min-h-screen w-full items-center justify-center bg-[var(--surface-base)] bg-cover bg-center bg-no-repeat bg-fixed px-6 py-12 sm:px-16"
      style={{ backgroundImage: "url('/imageLogin.png')" }}
    >
      <div className="flex w-full max-w-5xl flex-col items-center gap-10 md:flex-row md:items-center md:justify-evenly lg:gap-16">
        {/* LOGO Lado Esquerdo (Desktop) usando a variant large */}
        <BrandLogo
          variant="large"
          className="hidden w-full max-w-[300px] shrink-0 md:block lg:max-w-[500px]"
        />

        {/* Formulário Lado Direito */}
        <div className="w-full max-w-sm">
          {/* LOGO Lado Direito (Mobile) usando a variant small */}
          <BrandLogo variant="small" className="mb-8 md:hidden" />

          <form
            className="flex flex-col gap-5"
            onSubmit={handleSubmit}
            noValidate
          >
            <Input
              id="email"
              type="email"
              label="E-mail corporativo"
              placeholder="nome.sobrenome@empresa.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={fieldErrors.email}
            />

            <Input
              id="senha"
              type="password"
              label="Senha"
              placeholder="••••••••"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              error={fieldErrors.senha}
            />

            {apiError && (
              <p className="text-center text-sm font-medium text-red-400">
                {apiError}
              </p>
            )}

            <Button type="submit" loading={loading}>
              Entrar na Plataforma
            </Button>
          </form>

          <p className="mt-6 text-center text-xs text-white/60">
            Acesso restrito para colaboradores da PRO4TECH.
          </p>
        </div>
      </div>
    </div>
  )
}
