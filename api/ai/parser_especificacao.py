"""
Converte o texto de uma especificação no dicionário que o checklist (#8-1)
espera. Determinístico, sem IA.

Formatos aceitos (podem aparecer misturados):

1. Modelo oficial do assistente (system prompt de Épico/Feature/PBI):
       ÉPICO — Título
       Descrição: ...
       PBI — Verbo no infinitivo + objeto
       COMO UM ator
       EU QUERO ação
       PARA QUE benefício
       Cenário 1 — Nome
       DADO que ...
       QUANDO ...
       ENTÃO ...
2. Formato com dois-pontos: "Épico: Título", "História: ...", "Dado: ...".

Regras gerais:
- Um cabeçalho é "Chave — valor", "Chave - valor" ou "Chave: valor" no início
  da linha (Épico, Feature, PBI, Descrição, Objetivo, Escopo macro, Resultado
  esperado, Critérios de aceitação, História, Protótipo, Cenário, Dado,
  Quando, Então, Regras e observações).
- Linhas sem cabeçalho continuam o campo anterior. Itens de lista começam
  com "-", "*", "•" ou "1.".
- Dentro de um PBI, COMO UM / EU QUERO / PARA QUE (sem separador) formam a
  história, e DADO / QUANDO / ENTÃO também valem sem separador.
- Lacunas contam como campo vazio: "[não consta no contexto]" e campos do
  modelo ainda não preenchidos ("[Título da iniciativa]"). Assim o checklist
  aponta a falta em vez de aprová-la.
- Decoração de Markdown (#, **, `, cercas ``` e linhas ---) é ignorada.
"""

import re
import unicodedata

MODELO_ESPECIFICACAO = """ÉPICO — [Título da iniciativa]
Descrição: [contexto do que será entregue, público afetado e abrangência]
Objetivo: [valor ou resultado pretendido e por que o Épico é necessário]
Escopo macro:
- [grande grupo de capacidades 1]
- [grande grupo de capacidades 2]
Resultado esperado: [estado desejado após a conclusão]
Critérios de aceitação:
- [condição ampla e verificável 1]
- [condição ampla e verificável 2]

FEATURE — [Título da capacidade]
Descrição: [capacidade funcional, contexto e principais comportamentos]
Objetivo: [benefício funcional ou operacional esperado]
Critérios de aceitação:
- [regra geral 1]
- [regra geral 2]

PBI — [Verbo no infinitivo + objeto da ação]
COMO UM [tipo de usuário ou ator]
EU QUERO [ação ou capacidade desejada]
PARA QUE [benefício, resultado ou motivo de negócio]
Protótipo ou referência visual: [quando houver interface relevante]
Cenário 1 — [Nome do cenário]
DADO que [estado inicial ou contexto]
QUANDO [ação ou evento]
ENTÃO [comportamento ou resultado esperado]
Cenário 2 — [Nome do cenário de erro]
DADO que [contexto alternativo]
QUANDO [ação ou evento]
ENTÃO [resultado esperado]
Regras e observações: [somente se necessário]"""

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
    "prototipo ou referencia visual": "prototipo",
    "prototipo": "prototipo",
    "referencia visual": "prototipo",
    "cenario": "cenario",
    "dado": "dado",
    "quando": "quando",
    "entao": "entao",
    "regras e observacoes": "regras_observacoes",
    "observacoes": "regras_observacoes",
}
_CAMPOS_LISTA = {"escopo_macro", "criterios_aceitacao"}
_ESTRUTURAIS = {"epico", "feature", "pbi"}
_GHERKIN = ("dado", "quando", "entao")
_ROTULO_GHERKIN = {"dado": "DADO", "quando": "QUANDO", "entao": "ENTÃO"}

# "Chave — valor", "Chave – valor", "Chave - valor" (hífen com espaços) ou "Chave: valor".
# A chave para no primeiro separador; o resto da linha é o valor.
_RX_CABECALHO = re.compile(
    r"^(?P<chave>[^:—–\n]{1,45}?)\s*(?::|—|–|\s-\s)\s*(?P<valor>.*)$"
)
_RX_ITEM = re.compile(r"^(?:[-*•]|\d+[.)])\s+(?P<texto>.*)$")
_RX_GHERKIN_SEM_SEPARADOR = re.compile(
    r"^(?P<chave>dado|quando|então|entao)\b[\s,:\-]*(?P<valor>.*)$",
    re.IGNORECASE,
)
# História em linhas soltas: COMO UM ... / EU QUERO ... / PARA QUE ...
_RX_HISTORIA_LINHA = re.compile(
    r"^(?P<kw>como(?:\s+(?:um|uma))?|eu\s+quero|eu\s+desejo|quero|desejo"
    r"|para\s+que)\b(?P<resto>.*)$",
    re.IGNORECASE,
)
# Lacuna: "[não consta no contexto]" ou campo do modelo ainda em branco
# ("[Título da iniciativa]", "que [estado inicial]").
_RX_PLACEHOLDER = re.compile(r"^(?:que\s+)?\[[^\]]*\]\.?$", re.IGNORECASE)
_RX_REGUA = re.compile(r"^\s*(?:[-_*=]\s*){3,}$")
# Cenário completo escrito numa linha só: o checklist aceita como critério em texto.
_RX_CENARIO_INLINE = re.compile(r"\bdado\b.*?\bquando\b.*?\bentao\b", re.DOTALL)


def _sem_acento(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c))


def _limpar_linha(linha: str) -> str:
    """Tira a decoração de Markdown que atrapalha o reconhecimento."""
    linha = re.sub(r"^\s*#{1,6}\s*", "", linha)
    linha = re.sub(r"^\s*>\s?", "", linha)
    return linha.replace("**", "").replace("__", "").replace("`", "").strip()


def _valor(texto: str) -> str:
    """Valor do campo; lacunas ("[não consta no contexto]") viram vazio."""
    texto = (texto or "").strip()
    return "" if _RX_PLACEHOLDER.match(texto) else texto


def _cabecalho(linha: str):
    """(chave_canonica, valor) se a linha começa com um cabeçalho conhecido."""
    m = _RX_CABECALHO.match(linha)
    if not m:
        return None
    chave = re.sub(r"\s+", " ", _sem_acento(m.group("chave")).lower()).strip()
    chave = re.sub(r"[\s#\d.\-]+$", "", chave)  # "Cenário 1", "PBI-2" -> "cenario", "pbi"
    canonica = _CHAVES.get(chave)
    if canonica is None:
        return None
    return canonica, m.group("valor").strip()


def _continuar(campo, linha: str) -> None:
    container, chave, eh_lista = campo
    m = _RX_ITEM.match(linha)
    texto = _valor(m.group("texto") if m else linha)
    if not texto:  # lacuna não acrescenta nada
        return
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
    """True se o texto tem ao menos um Épico/Feature/PBI e mais um cabeçalho."""
    estruturais = total = 0
    for bruta in (texto or "").splitlines():
        cab = _cabecalho(_limpar_linha(bruta))
        if cab:
            total += 1
            if cab[0] in _ESTRUTURAIS:
                estruturais += 1
    return estruturais >= 1 and total >= 2


def extrair_especificacao(texto: str):
    """Devolve (dados, observacoes): o dicionário do checklist e avisos sobre
    trechos que não puderam ser associados a nenhum item."""
    dados = {"epicos": []}
    observacoes = []
    soltas = 0
    epico = feature = pbi = cenario = None
    campo = None  # (container, chave, eh_lista) do campo que continua na próxima linha

    for bruta in (texto or "").splitlines():
        if bruta.strip().startswith("```") or _RX_REGUA.match(bruta):
            continue
        linha = _limpar_linha(bruta)
        if not linha:
            continue

        cab = _cabecalho(linha)
        chave, valor = cab if cab else (None, None)
        if valor is not None:
            valor = _valor(valor)

        if chave is None and pbi is not None:
            # História em linhas soltas: COMO UM / EU QUERO / PARA QUE.
            h = _RX_HISTORIA_LINHA.match(linha)
            if h and cenario is None and (campo is None or campo[1] == "historia"):
                if _valor(h.group("resto")):  # linha com lacuna não entra na história
                    pbi["historia"] = f"{pbi.get('historia', '')} {linha}".strip()
                    campo = (pbi, "historia", False)
                continue

            # "Dado que...", "Quando...", "Então..." sem separador.
            g = _RX_GHERKIN_SEM_SEPARADOR.match(linha)
            if g:
                if _RX_CENARIO_INLINE.search(_sem_acento(linha).lower()):
                    pbi.setdefault("criterios_aceitacao", []).append(linha)
                    campo = (pbi, "criterios_aceitacao", True)
                    continue
                chave = _sem_acento(g.group("chave")).lower()
                valor = _valor(g.group("valor"))

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

        elif chave is not None:  # descricao, objetivo, historia, prototipo, listas...
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
                if valor:
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