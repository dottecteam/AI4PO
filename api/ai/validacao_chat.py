import re

from .checklist import resumo_validacao
from .parser_especificacao import (
    MODELO_ESPECIFICACAO,
    extrair_especificacao,
    parece_especificacao,
)

_RX_COMANDO = re.compile(r"^/validar(\s|$)", re.IGNORECASE)

MENSAGEM_SEM_MODELO = (
    "Não encontrei nenhum Épico, Feature ou PBI no texto. Escreva a "
    "especificação neste modelo e envie novamente com `/validar`:\n\n"
    f"```\n{MODELO_ESPECIFICACAO}\n```"
)


def detectar_especificacao(message: str, documento_texto: str):
    """Devolve o texto a validar, ou None se a mensagem não é uma especificação.
    Devolve '' quando o usuário digitou /validar sem nenhum texto."""
    msg = (message or "").strip()
    doc = (documento_texto or "").strip()
    if _RX_COMANDO.match(msg):
        corpo = msg[len("/validar"):].strip()
        return corpo or doc
    if parece_especificacao(doc):
        return doc
    if parece_especificacao(msg):
        return msg
    return None


def montar_validacao(texto: str):
    """Dados do cartão, ou None se nada no texto foi reconhecido."""
    dados, observacoes = extrair_especificacao(texto)
    if not dados["epicos"]:
        return None

    pendencias = resumo_validacao(dados)["pendencias"]
    falhas = [p for p in pendencias if not p["ok"]]

    def _cartao(p):
        return {k: p[k] for k in ("regra", "nivel", "item", "mensagem")}

    return {
        "conforme": not any(p["severidade"] == "erro" for p in falhas),
        "total_regras": len(pendencias),
        "aprovadas": sum(1 for p in pendencias if p["ok"]),
        "erros": [_cartao(p) for p in falhas if p["severidade"] == "erro"],
        "avisos": [_cartao(p) for p in falhas if p["severidade"] == "aviso"],
        "observacoes": observacoes,
    }


def resumo_curto(v: dict) -> str:
    if v["conforme"]:
        texto = "Validação concluída: a especificação está em conformidade com o guia."
        if v["avisos"]:
            texto += f" Há {len(v['avisos'])} aviso(s) para revisar."
        return texto
    return (f"Validação concluída: {len(v['erros'])} erro(s) e "
            f"{len(v['avisos'])} aviso(s) encontrados.")


def para_markdown(v: dict) -> str:
    """Versão em texto, gravada no histórico (o cartão não é persistido)."""
    def _linha(p):
        return f"- `{p['regra']}` ({p['nivel']} · {p['item']}): {p['mensagem']}"

    linhas = [
        "**Resultado da validação:** "
        + ("especificação em conformidade com o guia."
           if v["conforme"] else "há pendências."),
        f"{v['aprovadas']} de {v['total_regras']} regras aprovadas.",
    ]
    if v["erros"]:
        linhas += ["", "**Erros (bloqueiam a conformidade)**"]
        linhas += [_linha(p) for p in v["erros"]]
    if v["avisos"]:
        linhas += ["", "**Avisos**"]
        linhas += [_linha(p) for p in v["avisos"]]
    if v["observacoes"]:
        linhas += ["", "**Observações**"]
        linhas += [f"- {o}" for o in v["observacoes"]]
    return "\n".join(linhas)