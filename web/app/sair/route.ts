import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

// Apaga os cookies de sessão e volta para o login
export function GET(request: NextRequest) {
  const resposta = NextResponse.redirect(new URL("/?error=unauthorized", request.url))
  resposta.cookies.delete("access_token")
  resposta.cookies.delete("refresh_token")
  return resposta
}