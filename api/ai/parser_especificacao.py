"""
Converte o texto de uma especificação, escrito no modelo com cabeçalhos
fixos, no dicionário que o checklist (#8-1) espera. Determinístico, sem IA.

Regras do formato:
- Um cabeçalho é "Chave: valor" no início da linha (Épico, Feature, PBI,
  Descrição, Objetivo, Escopo macro, Resultado esperado, Critérios de
  aceitação, História, Cenário, Dado, Quando, Então).
- Linhas que não começam com cabeçalho continuam o campo anterior.
- Itens de lista começam com "-", "*", "•" ou "1.".
- Dentro de um PBI, "Dado que...", "Quando...", "Então..." também valem
  sem os dois-pontos.
"""

import re
import unicodedata

MODELO_ESPECIFICACAO = """Épico: <título do épico>
Descrição: <o que o épico entrega, em nível macro>
Objetivo: <por que ele existe>
Escopo macro:
- <capacidade 1>
- <capacidade 2>
Resultado esperado: <resultado final para o negócio ou usuário>
Critérios de aceitação:
- <critério macro 1>

Feature: <título da feature>
Descrição: <o que a feature entrega>
Objetivo: <por que ela existe>
Critérios de aceitação:
- <regra geral 1>

PBI: <verbo no infinitivo + objeto>
História: Como <papel>, eu quero <ação>, para que <benefício>.
Cenário: <nome do cenário principal>
Dado: <estado inicial>
Quando: <ação>
Então: <resultado esperado>
Cenário: <nome do cenário de erro>
Dado: <estado inicial>
Quando: <ação>
Então: <resultado esperado>"""

_CHAVES = {
    "epico": "epico",
    "feature": "feature",
    "pbi": "pbi",
    "descricao": "descricao",
    "objetivo": "objetivo",
    "escopo macro": "escopo_macro",
    "escopo": "escopo_macro",
    "resultado esperado": "resultado_esperado",
    "criterios de aceitacao": "criterios_aceitacao",
    "criterio de aceitacao": "criterios_aceitacao",
    "criterios": "criterios_aceitacao",
    "historia": "historia",
    "historia do usuario": "historia",
    "cenario": "cenario",
    "dado": "dado",
    "quando": "quando",
    "entao": "entao",
}
_CAMPOS_LISTA = {"escopo_macro", "criterios_aceitacao"}
_ESTRUTURAIS = {"epico", "feature", "pbi"}
_GHERKIN = ("dado", "quando", "entao")
_ROTULO_GHERKIN = {"dado": "DADO", "quando": "QUANDO", "entao": "ENTÃO"}

_RX_CABECALHO = re.compile(r"^(?P<chave>[^:\n]{1,40}?)\s*:\s*(?P<valor>.*)$")
_RX_ITEM = re.compile(r"^(?:[-*•]|\d+[.)])\s+(?P<texto>.*)$")
_RX_GHERKIN_SEM_DOIS_PONTOS = re.compile(
    r"^(?P<chave>dado|quando|então|entao)\b[\s,:\-]*(?P<valor>.*)$",
    re.IGNORECASE,
)
#checklist aceita como critério em texto.
_RX_CENARIO_INLINE = re.compile(r"\bdado\b.*?\bquando\b.*?\bentao\b", re.DOTALL)


def _sem_acento(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c))


def _limpar_linha(linha: str) -> str:
    linha = re.sub(r"^\s*#{1,6}\s*", "", linha)
    return linha.replace("**", "").replace("__", "").strip()


def _cabecalho(linha: str):
    m = _RX_CABECALHO.match(linha)
    if not m:
        return None
    chave = re.sub(r"\s+", " ", _sem_acento(m.group("chave")).lower()).strip()
    chave = re.sub(r"[\s#\d.\-]+$", "", chave)
    canonica = _CHAVES.get(chave)
    if canonica is None:
        return None
    return canonica, m.group("valor").strip()


def _continuar(campo, linha: str) -> None:
    container, chave, eh_lista = campo
    m = _RX_ITEM.match(linha)
    texto = m.group("texto").strip() if m else linha
    if eh_lista:
        itens = container[chave]
        if m or not itens:
            itens.append(texto)
        else:
            itens[-1] = f"{itens[-1]} {texto}"
    else:
        atual = container.get(chave, "")
        container[chave] = f"{atual} {texto}".strip()


def parece_especificacao(texto: str) -> bool:
    estruturais = total = 0
    for bruta in (texto or "").splitlines():
        cab = _cabecalho(_limpar_linha(bruta))
        if cab:
            total += 1
            if cab[0] in _ESTRUTURAIS:
                estruturais += 1
    return estruturais >= 1 and total >= 2


def extrair_especificacao(texto: str):
    dados = {"epicos": []}
    observacoes = []
    soltas = 0
    epico = feature = pbi = cenario = None
    campo = None

    for bruta in (texto or "").splitlines():
        linha = _limpar_linha(bruta)
        if not linha:
            continue

        cab = _cabecalho(linha)
        chave, valor = cab if cab else (None, None)

        # Dentro de um PBI: "Dado que...", "Quando...", "Então..." sem dois-pontos.
        if chave is None and pbi is not None:
            g = _RX_GHERKIN_SEM_DOIS_PONTOS.match(linha)
            if g:
                if _RX_CENARIO_INLINE.search(_sem_acento(linha).lower()):
                    pbi.setdefault("criterios_aceitacao", []).append(linha)
                    campo = (pbi, "criterios_aceitacao", True)
                    continue
                chave = _sem_acento(g.group("chave")).lower()
                valor = g.group("valor").strip()

        if chave == "epico":
            epico = {"titulo": valor, "features": []}
            dados["epicos"].append(epico)
            feature = pbi = cenario = None
            campo = None

        elif chave == "feature":
            if epico is None:
                epico = {"features": []}
                dados["epicos"].append(epico)
            feature = {"titulo": valor, "pbis": []}
            epico["features"].append(feature)
            pbi = cenario = None
            campo = None

        elif chave == "pbi":
            if feature is None:
                if epico is None:
                    epico = {"features": []}
                    dados["epicos"].append(epico)
                feature = {"pbis": []}
                epico["features"].append(feature)
            pbi = {"titulo": valor, "cenarios": []}
            feature["pbis"].append(pbi)
            cenario = None
            campo = None

        elif chave == "cenario":
            campo = None
            if pbi is None:
                observacoes.append(
                    f"O cenário '{valor}' está fora de um PBI e foi ignorado.")
                continue
            cenario = {"nome": valor, "dado": "", "quando": "", "entao": ""}
            pbi["cenarios"].append(cenario)

        elif chave in _GHERKIN:
            if pbi is None:
                observacoes.append(
                    f"'{_ROTULO_GHERKIN[chave]}' fora de um PBI foi ignorado.")
                campo = None
                continue
            novo = cenario is None or (
                chave == "dado" and any(cenario[k] for k in _GHERKIN))
            if novo:  # sequência de cenários sem a linha "Cenário:"
                cenario = {"nome": "", "dado": "", "quando": "", "entao": ""}
                pbi["cenarios"].append(cenario)
            cenario[chave] = valor
            campo = (cenario, chave, False)

        elif chave is not None:  # descricao, objetivo, historia, listas...
            rotulo = chave.replace("_", " ")
            if chave == "historia" and pbi is None:
                observacoes.append("Uma história fora de um PBI foi ignorada.")
                campo = None
                continue
            alvo = pbi if pbi is not None else (
                feature if feature is not None else epico)
            if alvo is None:
                observacoes.append(
                    f"O campo '{rotulo}' veio antes de qualquer Épico, Feature "
                    "ou PBI e foi ignorado.")
                campo = None
                continue
            cenario = None
            if chave in _CAMPOS_LISTA:
                lista = alvo.setdefault(chave, [])
                if valor:
                    lista.append(valor)
                campo = (alvo, chave, True)
            else:
                alvo[chave] = valor
                campo = (alvo, chave, False)

        else:  # linha sem cabeçalho: continua o campo anterior
            if campo is None:
                soltas += 1
                continue
            _continuar(campo, linha)

    if soltas:
        observacoes.append(
            f"{soltas} linha(s) fora de um campo reconhecido foram ignoradas.")
    return dados, observacoes