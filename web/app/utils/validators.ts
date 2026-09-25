const emailFormatado = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validarEmail(email: string): string | undefined {
  if (!email) return "Informe o e-mail.";
  if (!emailFormatado.test(email)) return "E-mail inválido.";
  return undefined;
}

export function validarSenha(senha: string): string | undefined {
  if (!senha) return "Informe a senha.";
  return undefined;
}