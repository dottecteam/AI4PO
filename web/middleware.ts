import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Pega o token de acesso dos cookies
  const token = request.cookies.get('access_token')?.value;

  // Qual é a rota que o usuário está tentando acessar?
  const isLoginPage = request.nextUrl.pathname === '/';
  
  // Rotas que queremos proteger (ex: /dashboard, /projetos, etc)
  // Como a raiz '/' é o login, vamos proteger tudo que NÃO for a raiz
  const isProtectedRoute = !isLoginPage;

  // Se a rota for protegida e NÃO tiver token, redireciona pro login (/)
  if (isProtectedRoute && !token) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  // Se o usuário TIVER o token e tentar acessar o login (/), joga ele pro painel
  if (isLoginPage && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Se tiver tudo certo, deixa a requisição seguir normalmente
  return NextResponse.next();
}

// Configura em quais rotas o middleware deve rodar
export const config = {
  // Ignora rotas de API do Next, arquivos estáticos, imagens do Next e o favicon
  matcher: ['/((?!api|_next/static|_next/image|.*\\.png$).*)'],
};