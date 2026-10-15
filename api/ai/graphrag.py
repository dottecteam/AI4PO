"""GraphRAG: grafo de conhecimento extraído dos documentos indexados.

Pipeline de ingestão (task #13-1):
  1. extrair entidades e relações de cada chunk com o LLM;
  2. deduplicar por chave canônica dentro do projeto;
  3. gravar arestas tipadas com confiança e evidências (chunks de origem).

Detecção de comunidades e retrieval chegam nas tasks #13-2/#13-3.
"""

import json
import re
import time
import unicodedata

import requests
from decouple import config
from django.db import transaction
from django.db.models.functions import Length

from ai.models import ChunkDoc, Entidade, Relacao

OLLAMA_URL = config("OLLAMA_URL", default="http://localhost:11434")
# Para extração usamos o modelo base (sem persona), que segue JSON melhor.
MODELO_GRAFO = config("GRAPH_MODEL", default="llama3.2:3b")
KEEP_ALIVE = config("OLLAMA_KEEP_ALIVE", default="30m")


class ErroDeGrafo(Exception):
    """Modelo de grafo indisponível ou resposta inválida."""


def _chat(prompt, system="", num_predict=512, temperature=0.0, formato=None, stop=None):
    """Chamada simples ao Ollama (sem persona) para extração.

    Latência: temperature=0 elimina variância, num_predict limita a saída,
    keep_alive mantém o modelo residente na GPU (sem cold-load por chamada).
    """
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    opts = {"num_predict": num_predict, "temperature": temperature}
    if stop:
        opts["stop"] = stop
    payload = {
        "model": MODELO_GRAFO,
        "messages": messages,
        "stream": False,
        "keep_alive": KEEP_ALIVE,
        "options": opts,
    }
    if formato:
        payload["format"] = formato
    try:
        resposta = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        resposta.raise_for_status()
        return resposta.json()["message"]["content"]
    except (requests.RequestException, KeyError) as erro:
        raise ErroDeGrafo(f"Falha ao chamar o modelo de grafo em {OLLAMA_URL}: {erro}") from erro


# Prompt enxuto: tipos + regras, sem exemplo (economiza ~400 tokens de contexto
# por chamada — em ingestão com centenas de chunks, isso é horas de GPU).
_PROMPT_EXTRACAO = """\
Extraia entidades e relacoes do texto. Responda APENAS JSON.

Formato: {"entidades":[{"nome":"","tipo":"","descricao":""}],"relacoes":[{"origem":"","destino":"","tipo":"","confianca":0.8,"descricao":""}]}

Tipos de entidade PERMITIDOS (use apenas um destes): pessoa | decisao | requisito | sprint | sistema | artefato | indicador | conceito
Tipos de relacao PERMITIDOS: depende_de | implementa | decidido_em | pertence_a | resolve | bloqueia | deriva_de | menciona

Regras rigidas:
- 'nome' e um substantivo curto (maximo 4 palavras) que identifica a coisa. NUNCA use verbos (ex.: 'muda', 'aprovou'), datas, horarios, caminhos de arquivo ou texto de navegacao/cabecalho.
- Se o mesmo conceito aparece mais de uma vez, cite-o uma unica vez no singular.
- Nao crie entidade para palavra generica isolada (ex.: 'sistema', 'dados', 'projeto', 'time').
- Somente relacoes explicitas no texto. Nao invente. Os nomes das relacoes devem bater com as entidades listadas.
- 'confianca' e um numero de 0 a 1 indicando quao clara e a relacao no texto.
- Max 8 entidades, 10 relacoes.
"""

# Taxonomia fechada: tipo fora da lista vira 'conceito' (evita entidades verbo).
_TIPOS_PERMITIDOS = {"pessoa", "decisao", "requisito", "sprint", "sistema", "artefato", "indicador", "conceito"}
# Lixo clássico do extrator: datas, breadcrumbs, arquivos e placeholders do modelo.
_RX_LIXO = re.compile(r"\.(md|pdf|txt|json|py|ts|tsx)$|^realit\s*#|\bsem_dado\b", re.IGNORECASE)
_RX_DATA = re.compile(r"^\d{1,2}[/\-.]\d{1,2}([/\-.]\d{2,4})?$")
# Verbos conjugados que o modelo às vezes devolve como 'entidade' (heurística pt).
_RX_VERBO = re.compile(r"(ou|iu|aram|iam|ava|ando|endo|ido)$", re.IGNORECASE)
# Palavras demasiado genericas para virar no.
_NOMES_GENERICOS = {"sistema", "dados", "projeto", "coisa", "item", "parte", "time", "equipe", "empresa", "produto", "documento", "texto", "informacao", "analise", "processo", "api", "node", "endpoint", "indicador", "modulo", "componente", "requisito"}
# Infinitivos comuns que o modelo devolve como "entidade" — lista explicita para
# nao rejeitar termos validos em ingles que so terminam em -er/-ar (server, parser).
_VERBOS_BLOQUEADOS = {"gerar", "validar", "indexar", "criar", "definir", "usar", "fazer", "tratar", "extrair", "gerenciar", "configurar", "implementar", "registrar", "armazenar", "processar", "retornar", "exibir", "adicionar", "remover", "atualizar", "buscar", "salvar", "enviar", "receber", "executar", "realizar", "analisar", "verificar", "documentar", "notificar"}
# Regra do prompt ("nome no máximo 4 palavras") aplicada com folga: nomes
# próprios legítimos passam de 4 palavras ("Cooperativa de Crédito Vale Norte");
# o teto pega as frases-verbete que o modelo devolve (~7+ palavras).
_MAX_WORDS_NOME = 6


def _chave_canonica(nome):
    """Chave de deduplicação: minúscula, sem acento, sem pontuação e sem plural óbvio."""
    t = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9\s-]", " ", t)
    palavras = t.split()
    while palavras and palavras[0] in ("o", "a", "os", "as", "um", "uma", "de", "do", "da", "e"):
        palavras = palavras[1:]
    palavras = [w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("us") else w for w in palavras]
    return " ".join(palavras).strip()


def _eh_lixo(nome):
    """Rejeita o que não deve virar nó: datas, breadcrumbs, verbos, frases e genéricos.

    É o guardião de "dados de valores reais": nó de lixo polui comunidade e
    degrada a resposta do chat na ponta (retrieval recupera o que a ingestão deixou passar).
    """
    n = (nome or "").strip()
    if len(n) < 3 or _RX_LIXO.search(n) or _RX_DATA.match(n):
        return True
    if " " not in n and _RX_VERBO.search(n):
        return True
    if n.isupper() and len(n) <= 3:
        return True
    # O prompt pede nome de até 4 palavras; sem cobra no código, o modelo
    # devolve frases inteiras ("autenticação só na sprint 3 e com jwt") como nó.
    if len(n.split()) > _MAX_WORDS_NOME:
        return True
    # Compara o nome cru E a chave canônica: 'dados' singulariza para 'dado' e
    # escaparia do filtro se checássemos só a chave.
    chave = _chave_canonica(n)
    return (
        n.lower() in _NOMES_GENERICOS
        or chave in _NOMES_GENERICOS
        or chave in _VERBOS_BLOQUEADOS
    )


def _extrair_json(bruto):
    """Recupera o primeiro objeto JSON válido, tolerando cercas markdown e lixo ao redor."""
    texto = bruto.strip()
    if texto.startswith("```"):
        texto = texto.split("```", 2)[1] if texto.count("```") >= 2 else texto.strip("`")
        texto = texto.removeprefix("json").removeprefix("JSON")
    ini = texto.find("{")
    if ini == -1:
        return None
    # Varredura de chaves balanceadas até fechar o objeto
    nivel = 0
    for i in range(ini, len(texto)):
        if texto[i] == "{":
            nivel += 1
        elif texto[i] == "}":
            nivel -= 1
            if nivel == 0:
                try:
                    return json.loads(texto[ini:i + 1])
                except json.JSONDecodeError:
                    return None
    return None  # JSON truncado (não fechou)


def extrair_grafo_do_texto(texto, teto=800, num_predict=600):
    """Pede ao LLM o dicionário {entidades, relacoes} de um trecho. Inválido vira vazio.

    JSON estrito primeiro (Ollama forçado a saída válida); se ainda vier lixo,
    uma única regrava sem modo JSON pega modelos que "conversam" melhor livres.
    Anti-alucinação: resposta fora do formato não gera grafo — preferimos
    lacuna (nada extraído) a dado inventado.
    """
    bruto = _chat(prompt=texto[:teto], system=_PROMPT_EXTRACAO, num_predict=num_predict, formato="json")
    dados = _extrair_json(bruto)
    if not isinstance(dados, dict):
        bruto = _chat(prompt=texto[:teto], system=_PROMPT_EXTRACAO, num_predict=num_predict)
        dados = _extrair_json(bruto)
    if not isinstance(dados, dict):
        return {"entidades": [], "relacoes": []}
    dados.setdefault("entidades", [])
    dados.setdefault("relacoes", [])
    return dados


def _obter_ou_criar_entidade(nome, tipo, descricao, projeto):
    """Cria/reaproveita entidade pela chave canônica dentro do projeto (deduplicação)."""
    bruto = (nome or "").strip()
    if not bruto or _eh_lixo(bruto):
        return None
    chave = _chave_canonica(bruto)
    if not chave or chave in _NOMES_GENERICOS:
        return None
    tipo_ok = (tipo or "").strip().lower()
    if tipo_ok not in _TIPOS_PERMITIDOS:
        tipo_ok = "conceito"
    ent = Entidade.objects.filter(chave=chave, projeto=projeto).first()
    if ent:
        return ent
    return Entidade.objects.create(
        nome=bruto[:255], chave=chave, tipo=tipo_ok, descricao=descricao or "", projeto=projeto
    )


def ingestir(limite=None, projeto_id=None, lote=1, documento_id=None):
    """Extrai entidades/relações de chunks em lotes (batching). Retorna métricas + tempo.

    Latência: o lote agrupa N chunks por chamada ao LLM (menos idas à GPU);
    chunks curtos (<150 chars) são pulados pois raramente rendem grafo.
    Não altera o estado do Documento: o grafo é uma camada sobre conteúdo
    já indexado pela pipeline de RAG (chunking + embeddings).
    Idempotência: deduplicação por chave canônica + get_or_create na tripla
    (origem, destino, tipo) — reingestir o mesmo doc não duplica arestas.
    """
    queryset = (
        ChunkDoc.objects
        .annotate(_n=Length("conteudo"))
        .filter(_n__gte=150)
        .select_related("projeto")
        .order_by("id")
    )
    if projeto_id:
        queryset = queryset.filter(projeto_id=projeto_id)
    if documento_id:
        queryset = queryset.filter(documento_id=documento_id)
    chunks = list(queryset[:limite] if limite else queryset)

    # Agrupar em lotes de `lote` chunks para reduzir chamadas ao LLM
    lotes = [chunks[i:i + lote] for i in range(0, len(chunks), lote)]

    t0 = time.perf_counter()
    n_ent = n_rel = 0
    for grupo in lotes:
        texto_junto = "\n\n---\n\n".join(c.conteudo[:1200] for c in grupo)
        # O teto acompanha o tamanho do lote: sem isso, chunks além do primeiro
        # seriam truncados para fora do prompt (lote pago, 1/3 do texto extraído).
        dados = extrair_grafo_do_texto(
            texto_junto, teto=800 * len(grupo), num_predict=min(1500, 600 * len(grupo))
        )
        projeto_ref = grupo[0].projeto  # todos os chunks do lote são do mesmo projeto
        # Um lote inteiro é um commit: mais rápido (sem fsync por INSERT) e, se a
        # ingestão morrer no meio, não fica entidade sem relação nem relação sem evidência.
        with transaction.atomic():
            mapa = {}  # chave canônica -> entidade
            for e in dados["entidades"][:15]:
                if not isinstance(e, dict):
                    continue
                ent = _obter_ou_criar_entidade(e.get("nome", ""), e.get("tipo", ""), e.get("descricao", ""), projeto_ref)
                if ent:
                    mapa[ent.chave] = ent
                    n_ent += 1
            for rel in dados["relacoes"][:20]:
                if not isinstance(rel, dict):
                    continue
                nome_o = (rel.get("origem", "") or "").strip()
                nome_d = (rel.get("destino", "") or "").strip()
                # Auto-criar entidade se o modelo referenciou nome não declarado
                o = mapa.get(_chave_canonica(nome_o))
                if not o and nome_o:
                    o = _obter_ou_criar_entidade(nome_o, "conceito", "", projeto_ref)
                    if o:
                        mapa[o.chave] = o
                        n_ent += 1
                d = mapa.get(_chave_canonica(nome_d))
                if not d and nome_d:
                    d = _obter_ou_criar_entidade(nome_d, "conceito", "", projeto_ref)
                    if d:
                        mapa[d.chave] = d
                        n_ent += 1
                if not o or not d or o == d:
                    continue
                try:
                    conf = float(rel.get("confianca", 0.7) or 0.7)
                except (TypeError, ValueError):
                    conf = 0.7
                conf = max(0.0, min(1.0, conf))
                obj, criado = Relacao.objects.get_or_create(
                    origem=o, destino=d, tipo=(rel.get("tipo", "menciona") or "menciona")[:50],
                    defaults={"descricao": rel.get("descricao", ""), "confianca": conf, "projeto": projeto_ref},
                )
                if not criado and conf > obj.confianca:
                    # Mesma tripla vista com mais clareza: confiança só sobe (monótono).
                    Relacao.objects.filter(pk=obj.pk).update(confianca=conf)
                # Evidências em massa: um INSERT agregado por lote, não N por aresta.
                Relacao.evidencias.through.objects.bulk_create(
                    [Relacao.evidencias.through(relacao_id=obj.id, chunkdoc_id=c.id) for c in grupo],
                    ignore_conflicts=True,
                )
                if criado:
                    n_rel += 1
    dur = round(time.perf_counter() - t0, 1)
    return {"chunks_processados": len(chunks), "lotes": len(lotes), "entidades": n_ent, "relacoes": n_rel, "segundos": dur}
