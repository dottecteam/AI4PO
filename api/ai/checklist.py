"""
Checklist de conformidade com o Guia de Especificação de Itens de Trabalho
(task #8-1).

Converte as regras do guia oficial (Épicos, Features e PBIs) em verificações
automáticas e determinísticas — sem IA. Cada regra produz uma Pendencia com
codigo da regra, item avaliado e mensagem objetiva quando falha.

Severidades:
- "erro": viola uma regra obrigatória do guia (bloqueia a conformidade);
- "aviso": recomendação do guia ou heurística (cobertura mínima, nível dos
  critérios, termos suspeitos).

Regras do guia NÃO automatizáveis por desenho (ficam a cargo da revisão
humana da equipe): tamanho/"pequeno o suficiente" do PBI (§1.1), protótipo
anexado quando necessário (§5.1/§8), conflito semântico entre níveis (§8)
e dependências explícitas (§8). Duplicação por cópia (§7) é detectada por
comparação normalizada com tolerância a pequenas variações.

A entrada é um dicionário com a estrutura do guia:
{
    "epicos": [
        {
            "titulo": str, "descricao": str, "objetivo": str,
            "escopo_macro": [str], "resultado_esperado": str,
            "criterios_aceitacao": [str],
            "features": [
                {
                    "titulo": str, "descricao": str, "objetivo": str,
                    "criterios_aceitacao": [str],
                    "pbis": [
                        {
                            "titulo": str,
                            "historia": str,
                            "criterios_aceitacao": [str],  # texto livre
                            "cenarios": [
                                {"nome": str, "dado": str, "quando": str,
                                 "entao": str}
                            ],
                        }
                    ],
                }
            ],
        }
    ]
}
"""

import re
import unicodedata
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher


@dataclass
class Pendencia:
    """Resultado de uma verificação do checklist."""

    regra: str          # código estável da regra (ex.: "PBI-TITULO-INFINITIVO")
    nivel: str          # "geral" | "épico" | "feature" | "pbi"
    item: str           # nome do item avaliado (título ou identificador)
    ok: bool
    mensagem: str = ""  # pendência objetiva quando ok=False
    severidade: str = "erro"  # "erro" | "aviso"


# Código ASCII estável usado na montagem do código das regras.
_CODIGO_NIVEL = {"épico": "EPICO", "feature": "FEATURE", "pbi": "PBI"}
# Rótulo legível usado nas mensagens exibidas ao usuário.
_ROTULO_NIVEL = {"épico": "Épico", "feature": "Feature", "pbi": "PBI"}

# Similaridade mínima (0-1) para considerar dois textos cópia um do outro.
_LIMIAR_DUPLICACAO = 0.9
# Máximo de ocorrências listadas numa mensagem antes de resumir com "(+N)".
_MAX_OCORRENCIAS = 4


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem pontuação, para comparações tolerantes."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", " ", texto.lower()).strip()


def _casa(regex: re.Pattern, texto: str) -> bool:
    """Busca tolerante a acentos/pontuação: normaliza antes de comparar."""
    return bool(regex.search(_normalizar(texto or "")))


def _txt(valor) -> str:
    """Devolve o valor se for string; qualquer outro tipo vira ''."""
    return valor if isinstance(valor, str) else ""


def _lista(valor) -> list:
    """Normaliza campos que podem vir como string, lista, tupla ou None."""
    if valor is None:
        return []
    if isinstance(valor, str):
        return [valor]
    if isinstance(valor, (list, tuple)):
        return list(valor)
    return []


def _dicts(valor) -> list:
    """Somente os itens dict de um campo que deveria ser lista de dicts."""
    return [v for v in _lista(valor) if isinstance(v, dict)]


def _strs(valor) -> list:
    """Somente as strings não vazias de um campo que deveria ser lista."""
    return [v for v in _lista(valor) if isinstance(v, str) and v.strip()]


def _esta_vazio(valor) -> bool:
    if valor is None:
        return True
    if isinstance(valor, str):
        return not valor.strip()
    if isinstance(valor, (list, tuple)):
        return all(_esta_vazio(item) for item in valor)
    if isinstance(valor, dict):
        return all(_esta_vazio(item) for item in valor.values())
    return False


def _identificar(item, padrao: str) -> str:
    item = item if isinstance(item, dict) else {}
    titulo = _txt(item.get("titulo")) or _txt(item.get("nome"))
    return titulo.strip() or padrao


def _resumir(itens, limite: int = _MAX_OCORRENCIAS) -> str:
    """Junta os primeiros itens e indica quantos ficaram de fora."""
    itens = list(itens)
    texto = ", ".join(itens[:limite])
    if len(itens) > limite:
        texto += f" (+{len(itens) - limite})"
    return texto


def _local(nivel: str, contexto: str) -> str:
    """Rótulo legível do item avaliado, para mensagens acionáveis."""
    rotulo = _ROTULO_NIVEL.get(nivel, nivel)
    return f"{rotulo} '{contexto}'" if contexto else rotulo


def _copia(a, b) -> bool:
    """True se os textos são iguais ou quase iguais após normalização."""
    a, b = _normalizar(_txt(a)), _normalizar(_txt(b))
    if not a or not b:
        return False
    return a == b or SequenceMatcher(None, a, b).ratio() >= _LIMIAR_DUPLICACAO


# ---------------------------------------------------------------------------
# Regras de conteúdo (extraídas do guia)
#
# Todas as regexes são aplicadas sobre texto já normalizado (minúsculo, sem
# acentos nem pontuação), por isso os padrões não têm acento.
# ---------------------------------------------------------------------------

# Título de PBI deve iniciar com verbo no infinitivo (seção 5 do guia).
# Além de -ar/-er/-ir, cobre os derivados de "pôr" (propor, repor, expor,
# compor...), que terminam em -or. `\w+por` exige ao menos uma letra antes,
# para não aceitar a preposição "por".
_RX_INFINITIVO = re.compile(r"^(?:\w*(?:ar|er|ir)|\w+por)\b", re.IGNORECASE)

# Substantivos comuns com terminação de infinitivo que passariam na
# heurística; recusados explicitamente para reduzir falso positivo.
_SUBSTANTIVOS_NAO_VERBAIS = {
    "lugar", "celular", "escolar", "solar", "impar", "par", "mulher",
    "super", "user", "header", "vapor",
}

# Títulos genéricos proibidos (seção 7: "Tela de usuários", "Ajustes no
# cadastro", "Melhoria do login").
_RX_TITULO_GENERICO = re.compile(
    r"^(tela|telas|ajuste|ajustes|melhoria|melhorias|arrumo|conserto)s?\b"
    r"|\b(etc|coisas|diversos)\b",
    re.IGNORECASE,
)

# Termos vagos sem condição verificável (seções 2 e 7), com flexão de gênero
# e número.
_RX_TERMOS_VAGOS = re.compile(
    r"\b(bonit[oa]s?|rapid[oa]s?|rapidamente|intuitiv[oa]s?|adequad[oa]s?|"
    r"corret[oa]s?|facil|faceis|eficient[ea]s?|modern[oa]s?|"
    r"amigavel|amigaveis|otim[oa]s?|bom|bons|boa|boas)\b",
    re.IGNORECASE,
)

# Marcadores de detalhe de tela em nível macro (seções 3.2/3.3 e 4.5).
_RX_DETALHE_TELA = re.compile(
    r"\b(botao|botoes|campos?|cliques?|dropdowns?|checkbox(?:es)?|"
    r"modais?|abas?|links?|bordas?)\b",
    re.IGNORECASE,
)

# Seção 7: textos que descrevem implementação em vez do resultado esperado
# ("Épico excessivamente técnico" cita bibliotecas, endpoints e tabelas).
# Aplicada somente a Épicos e Features — em PBIs esses termos costumam ser
# linguagem de negócio ("exibir em tabela").
_RX_DETALHE_IMPLEMENTACAO = re.compile(
    r"\b(endpoints?|bibliotecas?|frameworks?|banco de dados|codigo fonte|"
    r"scripts?|sql|sdk|rest|tabelas?)\b",
    re.IGNORECASE,
)

# Seção 5.4: cobertura mínima recomendada — validações, erros/
# indisponibilidade, permissões, estados alternativos. Radicais com \w*
# aceitam flexões (expirad\w* cobre expirada/expirados; erro\w* cobre erros).
# Só entram termos que quase sempre indicam condição de falha: palavras que
# também aparecem no caminho feliz ("formato", "sessão") ficaram de fora.
_RX_CENARIO_DE_ERRO = re.compile(
    r"\b(erro\w*|errad\w*|falha\w*|indisponivel\w*|invalid\w*|expirad\w*|"
    r"negad\w*|negar|bloquead\w*|impe[cd]\w*|sem permissao|nao autorizad\w*|"
    r"vazi\w*|ausencia\w*|limit\w*|obrigatori\w*|timeouts?|offline|"
    r"duplicad\w*)\b",
    re.IGNORECASE,
)

# Campos obrigatórios por nível (seções 3.2, 4.2 e 5.1 do guia).
_CAMPOS_EPICO = ("titulo", "descricao", "objetivo", "escopo_macro",
                 "resultado_esperado", "criterios_aceitacao")
_CAMPOS_FEATURE = ("titulo", "descricao", "objetivo", "criterios_aceitacao")
# No PBI, critérios de aceitação podem vir como lista 'criterios_aceitacao'
# e/ou como 'cenarios' estruturados — a presença é checada em regra própria.
_CAMPOS_PBI = ("titulo", "historia")

# História do usuário: COMO UM / EU QUERO / PARA QUE (seção 5.2). O modelo do
# guia usa "COMO UM ... EU QUERO", mas a checagem aceita variantes naturais de
# primeira pessoa (desejo/preciso/gostaria) e papel sem artigo
# ("Como PO, desejo...") para não reprovar texto bom por rigidez excessiva.
_RX_HISTORIA = re.compile(
    r"\bcomo\b.*?\b(eu\s+)?(quero|desejo|preciso|gostaria)\b.*?\bpara\s+que\b",
    re.IGNORECASE | re.DOTALL,
)

# Cenário DADO / QUANDO / ENTÃO (seção 5.3). 'DADO' dispensa a conjunção
# 'que': o que importa é o estado inicial seguido de ação e resultado.
_RX_CENARIO_INLINE = re.compile(
    r"\bdado\b.*?\bquando\b.*?\bentao\b",
    re.IGNORECASE | re.DOTALL,
)


def _verificar_campos(item: dict, campos: tuple, nivel: str, nome: str):
    """Checa presença dos campos obrigatórios da estrutura (seções 3.2/4.2/5.1)."""
    for campo in campos:
        yield Pendencia(
            regra=f"{_CODIGO_NIVEL.get(nivel, nivel.upper())}-CAMPO-"
                  f"{campo.upper().replace('_', '-')}",
            nivel=nivel,
            item=nome,
            ok=not _esta_vazio(item.get(campo)),
            mensagem=f"Falta o campo obrigatório '{campo}'.",
        )


def _titulo_em_infinitivo(titulo: str) -> bool:
    """Heurística do §5: a primeira palavra deve parecer verbo no infinitivo
    (-ar/-er/-ir ou derivado de 'pôr'), com recusa de substantivos comuns.
    É uma heurística: substantivos fora da lista de recusa ainda podem
    passar, e a revisão humana continua necessária."""
    palavras = _normalizar(titulo).split()
    if not palavras:
        return False
    primeira = palavras[0]
    if primeira in _SUBSTANTIVOS_NAO_VERBAIS:
        return False
    return bool(_RX_INFINITIVO.match(primeira))


# ---------------------------------------------------------------------------
# Verificações por nível
# ---------------------------------------------------------------------------

def _validar_epico(epico: dict):
    nome = _identificar(epico, "(Épico sem título)")
    yield from _verificar_campos(epico, _CAMPOS_EPICO, "épico", nome)

    # Seções 3.2/3.3: critérios e escopo macro do Épico não descem a detalhe
    # de tela/campo (isso pertence a um PBI).
    textos_macro = (_strs(epico.get("criterios_aceitacao"))
                    + _strs(epico.get("escopo_macro")))
    detalhe = [c for c in textos_macro if _casa(_RX_DETALHE_TELA, c)]
    yield Pendencia(
        regra="EPICO-CRITERIO-MACRO",
        nivel="épico",
        item=nome,
        ok=not detalhe,
        mensagem="Critérios/escopo macro descrevem detalhe de tela "
                 f"({len(detalhe)} ocorrência(s)); isso pertence a um PBI.",
        severidade="aviso",
    )

    # Seção 1.1: um Épico deve conter uma ou mais Features.
    features = _dicts(epico.get("features"))
    yield Pendencia(
        regra="EPICO-DECOMPOSICAO-FEATURES",
        nivel="épico",
        item=nome,
        ok=bool(features),
        mensagem="Épico sem nenhuma Feature; deve decompor-se em uma ou mais.",
    )

    for feature in features:
        yield from _validar_feature(feature)


def _validar_feature(feature: dict):
    nome = _identificar(feature, "(Feature sem título)")
    yield from _verificar_campos(feature, _CAMPOS_FEATURE, "feature", nome)

    # Seção 4.2: evitar títulos genéricos ("Ajustes", "Melhorias") também em
    # Features, não só em PBIs.
    yield Pendencia(
        regra="FEATURE-TITULO-NAO-GENERICO",
        nivel="feature",
        item=nome,
        ok=not _casa(_RX_TITULO_GENERICO, _txt(feature.get("titulo"))),
        mensagem="Título de Feature genérico; nomeie a capacidade funcional "
                 "(seção 4.2 do guia).",
        severidade="aviso",
    )

    # Seção 4.5: critérios da Feature em nível de regra geral, sem
    # micro-detalhe de tela.
    detalhe = [c for c in _strs(feature.get("criterios_aceitacao"))
               if _casa(_RX_DETALHE_TELA, c)]
    yield Pendencia(
        regra="FEATURE-CRITERIO-NIVEL",
        nivel="feature",
        item=nome,
        ok=not detalhe,
        mensagem=f"Critérios da Feature detalham tela ({len(detalhe)} "
                 "ocorrência(s)); detalhe de clique/campo pertence a PBIs "
                 "(seção 4.5).",
        severidade="aviso",
    )

    # Seção 1.1: uma Feature deve conter um ou mais PBIs.
    pbis = _dicts(feature.get("pbis"))
    yield Pendencia(
        regra="FEATURE-DECOMPOSICAO-PBIS",
        nivel="feature",
        item=nome,
        ok=bool(pbis),
        mensagem="Feature sem nenhum PBI; deve decompor-se em uma ou mais.",
    )

    # Seção 7: "Feature que é apenas um PBI grande" merece revisão de nível.
    # Com zero PBIs a regra acima já reporta o problema; aqui só interessa
    # o caso de exatamente um.
    yield Pendencia(
        regra="FEATURE-PBIS-INSUFICIENTES",
        nivel="feature",
        item=nome,
        ok=len(pbis) != 1,
        mensagem="Feature com um único PBI; verifique se a decomposição está "
                 "no nível certo (seção 7 do guia).",
        severidade="aviso",
    )

    for pbi in pbis:
        yield from _validar_pbi(pbi)


def _partes_cenario(cenario: dict) -> list:
    """[dado, quando, entao] já sem espaços; não-string vira ''."""
    return [_txt(cenario.get(p)).strip() for p in ("dado", "quando", "entao")]


def _extrair_cenarios(pbi: dict):
    """Aceita cenários estruturados ({dado, quando, entao}) ou texto livre em
    criterios_aceitacao com marcadores DADO/QUANDO/ENTÃO. Cenários totalmente
    vazios não contam (não inflacionam a checagem de cobertura)."""
    cenarios = []
    for c in _dicts(pbi.get("cenarios")):
        partes = _partes_cenario(c)
        if any(partes):
            cenarios.append(" ".join(partes))
    return cenarios, _strs(pbi.get("criterios_aceitacao"))


def _cenarios_em_texto(criterios: list) -> list:
    """Separa cada cenário DADO/QUANDO/ENTÃO escrito em texto livre.

    Um mesmo critério pode conter vários cenários; o texto é cortado a cada
    'DADO' e cada trecho completo conta como um cenário (mantendo o trecho
    inteiro, para que palavras de erro no ENTÃO sejam encontradas).
    """
    cenarios = []
    for criterio in criterios:
        for trecho in re.split(r"(?=\bdado\b)", _normalizar(criterio)):
            if _RX_CENARIO_INLINE.search(trecho):
                cenarios.append(trecho)
    return cenarios


def _validar_pbi(pbi: dict):
    nome = _identificar(pbi, "(PBI sem título)")
    yield from _verificar_campos(pbi, _CAMPOS_PBI, "pbi", nome)

    titulo = _txt(pbi.get("titulo")).strip()

    # Seção 5: título obrigatoriamente inicia com verbo no infinitivo.
    yield Pendencia(
        regra="PBI-TITULO-INFINITIVO",
        nivel="pbi",
        item=nome,
        ok=_titulo_em_infinitivo(titulo),
        mensagem="O título do PBI deve começar com verbo no infinitivo "
                 "(ex.: 'Cadastrar usuário').",
    )

    # Seção 7: proibido título genérico.
    yield Pendencia(
        regra="PBI-TITULO-NAO-GENERICO",
        nivel="pbi",
        item=nome,
        ok=not _casa(_RX_TITULO_GENERICO, titulo),
        mensagem="Título genérico; prefira uma ação objetiva no infinitivo.",
    )

    # Seção 5.2: história com ator (COMO...), intenção (QUERO/DESEJO...) e
    # benefício (PARA QUE...).
    yield Pendencia(
        regra="PBI-HISTORIA-ESTRUTURA",
        nivel="pbi",
        item=nome,
        ok=_casa(_RX_HISTORIA, _txt(pbi.get("historia"))),
        mensagem="A história do usuário deve seguir 'COMO [papel] ... "
                 "(EU) QUERO/DESEJO ... PARA QUE ...'.",
    )

    cenarios, texto_livre = _extrair_cenarios(pbi)
    cenarios_texto = _cenarios_em_texto(texto_livre)

    # Seção 5.1: o PBI deve ter critérios de aceitação (lista) e/ou cenários.
    yield Pendencia(
        regra="PBI-CAMPO-CRITERIOS",
        nivel="pbi",
        item=nome,
        ok=bool(cenarios) or bool(texto_livre),
        mensagem="Faltam critérios de aceitação ou cenários no PBI.",
    )

    # Seção 5.3: critérios escritos como cenários DADO/QUANDO/ENTÃO.
    yield Pendencia(
        regra="PBI-CRITERIO-CENARIO",
        nivel="pbi",
        item=nome,
        ok=bool(cenarios) or bool(cenarios_texto),
        mensagem="Nenhum critério de aceitação escrito como cenário "
                 "DADO/QUANDO/ENTÃO.",
    )

    # Cenários estruturados incompletos (falta uma das três partes); um
    # cenário totalmente vazio não é "incompleto", é ausência de cenário.
    incompletos = []
    for c in _dicts(pbi.get("cenarios")):
        partes = _partes_cenario(c)
        if any(partes) and not all(partes):
            incompletos.append(_txt(c.get("nome")).strip() or "(sem nome)")
    yield Pendencia(
        regra="PBI-CENARIO-COMPLETEZA",
        nivel="pbi",
        item=nome,
        ok=not incompletos,
        mensagem="Cenário(s) sem DADO/QUANDO/ENTÃO completo: "
                 f"{_resumir(incompletos)}.",
    )

    # Seção 5.4: cobertura mínima recomendada (caminho principal + erros).
    todos = cenarios + cenarios_texto
    cobriu_erro = any(_casa(_RX_CENARIO_DE_ERRO, c) for c in todos)
    yield Pendencia(
        regra="PBI-COBERTURA-ERROS",
        nivel="pbi",
        item=nome,
        ok=len(todos) >= 2 and cobriu_erro,
        mensagem="Cobertura recomendada não atingida: escreva ao menos dois "
                 "cenários, incluindo validações/erros (seção 5.4 do guia).",
        severidade="aviso",
    )


# ---------------------------------------------------------------------------
# Regras transversais
# ---------------------------------------------------------------------------

def _achar_termos(textos, regex, filtrar_niveis=None):
    """Coleta os termos detectados e os locais onde aparecem.

    `textos` são tuplas (nivel, contexto, texto). Retorna (termos, locais),
    ambos ordenados e sem repetição.
    """
    encontrados: set = set()
    locais: set = set()
    for nivel, contexto, t in textos:
        if filtrar_niveis is not None and nivel not in filtrar_niveis:
            continue
        for m in regex.finditer(_normalizar(t)):
            encontrados.add(m.group(0).lower())
            locais.add(_local(nivel, contexto))
    return sorted(encontrados), sorted(locais)


def _coletar_textos(epicos: list) -> list:
    """Todos os textos da especificação como tuplas (nivel, contexto, texto)."""
    textos = []

    def _coletar(nivel, item, contexto):
        for chave, valor in item.items():
            if chave in ("features", "pbis"):
                continue
            for v in _lista(valor):
                if isinstance(v, str) and v.strip():
                    textos.append((nivel, contexto, v))
                elif isinstance(v, dict):
                    # cenários: {dado, quando, entao, nome} também é texto
                    for parte in v.values():
                        if isinstance(parte, str) and parte.strip():
                            textos.append((nivel, contexto, parte))

    for epico in epicos:
        _coletar("épico", epico, _identificar(epico, "(Épico sem título)"))
        for feature in _dicts(epico.get("features")):
            _coletar("feature", feature,
                     _identificar(feature, "(Feature sem título)"))
            for pbi in _dicts(feature.get("pbis")):
                _coletar("pbi", pbi, _identificar(pbi, "(PBI sem título)"))
    return textos


def _achar_duplicacoes(epicos: list) -> list:
    """Cópias (iguais ou quase iguais) entre níveis, conforme o §7:
    'A Feature não deve copiar integralmente o Épico, e o PBI não deve
    repetir integralmente a Feature.'"""
    duplicados = []
    for epico in epicos:
        nome_e = _identificar(epico, "(Épico sem título)")
        criterios_e = _strs(epico.get("criterios_aceitacao"))
        for feature in _dicts(epico.get("features")):
            nome_f = _identificar(feature, "(Feature sem título)")
            if _copia(feature.get("descricao"), epico.get("descricao")):
                duplicados.append(
                    f"Feature '{nome_f}' repete a descrição do Épico '{nome_e}'")
            if _copia(feature.get("objetivo"), epico.get("objetivo")):
                duplicados.append(
                    f"Feature '{nome_f}' repete o objetivo do Épico '{nome_e}'")
            criterios_f = _strs(feature.get("criterios_aceitacao"))
            if any(_copia(f, e) for f in criterios_f for e in criterios_e):
                duplicados.append(
                    f"Feature '{nome_f}' repete critério(s) do Épico '{nome_e}'")
            for pbi in _dicts(feature.get("pbis")):
                criterios_p = _strs(pbi.get("criterios_aceitacao"))
                if any(_copia(p, f) for p in criterios_p for f in criterios_f):
                    duplicados.append(
                        f"PBI '{_identificar(pbi, '(PBI sem título)')}' repete "
                        f"critério(s) da Feature '{nome_f}'")
    return duplicados


def _validar_geral(dados: dict):
    """Regras transversais (seções 2 e 7): termos vagos em qualquer texto,
    detalhe de implementação só em Épicos/Features e duplicação entre níveis."""
    epicos = _dicts(dados.get("epicos"))
    yield Pendencia(
        regra="GERAL-TEM-EPICO",
        nivel="geral",
        item="(especificação)",
        ok=bool(epicos),
        mensagem="A especificação não contém nenhum Épico.",
    )

    textos = _coletar_textos(epicos)

    vagos, onde_vagos = _achar_termos(textos, _RX_TERMOS_VAGOS)
    yield Pendencia(
        regra="GERAL-SEM-TERMO-VAGO",
        nivel="geral",
        item="(especificação)",
        ok=not vagos,
        mensagem=f"Termos vagos sem condição verificável: {_resumir(vagos)} "
                 f"em {_resumir(onde_vagos)} (seção 2 do guia).",
        severidade="aviso",
    )

    # Seção 7: descrever o resultado esperado, não a implementação. Em PBIs
    # esses termos costumam ser linguagem de negócio, então a regra avalia
    # apenas Épicos e Features.
    tecnicos, onde_tecnicos = _achar_termos(
        textos, _RX_DETALHE_IMPLEMENTACAO, filtrar_niveis=("épico", "feature"))
    yield Pendencia(
        regra="GERAL-SEM-DETALHE-IMPLEMENTACAO",
        nivel="geral",
        item="(especificação)",
        ok=not tecnicos,
        mensagem="Textos descrevem implementação em vez do resultado "
                 f"esperado: {_resumir(tecnicos)} em {_resumir(onde_tecnicos)} "
                 "(seção 7 do guia; exceto quando a tecnologia for restrição "
                 "explícita).",
        severidade="aviso",
    )

    duplicados = _achar_duplicacoes(epicos)
    yield Pendencia(
        regra="GERAL-DUPLICACAO-NIVEIS",
        nivel="geral",
        item="(especificação)",
        ok=not duplicados,
        mensagem="Texto duplicado entre níveis (seção 7): "
                 f"{'; '.join(duplicados[:_MAX_OCORRENCIAS])}"
                 + (f" (+{len(duplicados) - _MAX_OCORRENCIAS})"
                    if len(duplicados) > _MAX_OCORRENCIAS else "")
                 + ".",
        severidade="aviso",
    )


# ---------------------------------------------------------------------------
# API do checklist
# ---------------------------------------------------------------------------

def validar_especificacao(dados: dict) -> list:
    """Roda todas as verificações do checklist e retorna a lista de Pendencia."""
    if not isinstance(dados, dict):
        return [Pendencia(regra="GERAL-ESTRUTURA", nivel="geral",
                          item="(especificação)", ok=False,
                          mensagem="A entrada deve ser um dicionário com a "
                                   "chave 'epicos'.")]
    pendencias = list(_validar_geral(dados))
    for epico in _dicts(dados.get("epicos")):
        pendencias.extend(_validar_epico(epico))
    # Regra aprovada não tem pendência: a mensagem só acompanha falha.
    for p in pendencias:
        if p.ok:
            p.mensagem = ""
    return pendencias


def resumo_validacao(dados: dict) -> dict:
    """Resumo consumível pela rota de validação (task #8-2):

    {
        "conforme": bool,          # True se nenhum "erro" pendente
        "erros": [...], "avisos": [...],
        "pendencias": [dict...]    # serialização das Pendencia completas
    }
    """
    pendencias = validar_especificacao(dados)
    erros = [p for p in pendencias if not p.ok and p.severidade == "erro"]
    avisos = [p for p in pendencias if not p.ok and p.severidade == "aviso"]
    return {
        "conforme": not erros,
        "erros": [f"[{p.nivel}] {p.item}: {p.mensagem}" for p in erros],
        "avisos": [f"[{p.nivel}] {p.item}: {p.mensagem}" for p in avisos],
        "pendencias": [asdict(p) for p in pendencias],
    }