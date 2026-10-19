"""GraphRAG: grafo de conhecimento extraído dos documentos indexados.

Pipeline de ingestão (task #13-1):
  1. extrair entidades e relações de cada chunk com o LLM;
  2. deduplicar por chave canônica dentro do projeto;
  3. gravar arestas tipadas com confiança e evidências (chunks de origem).

Detecção de comunidades na task #13-2; retrieval chega na #13-3.
"""

import json
import re
import time
import unicodedata
from collections import defaultdict

import requests
from decouple import config
from django.db import transaction
from django.db.models.functions import Length

from ai.models import ChunkDoc, Entidade, Comunidade, Relacao

OLLAMA_URL = config("OLLAMA_URL", default="http://localhost:11434")
# Para extração usamos o modelo base (sem persona), que segue JSON melhor.
# O default acompanha o modelo realmente usado nos testes locais (GRAPH_MODEL no .env).
MODELO_GRAFO = config("GRAPH_MODEL", default="qwen2.5:7b")
KEEP_ALIVE = config("OLLAMA_KEEP_ALIVE", default="30m")
# Saída longa (schema + descrições) rende 150-230s a ~11-17 tokens/s no 7B: o teto
# fixo de 120s matava o lote e jogava fora a inferência já paga no caminho.
CHAT_TIMEOUT = float(config("OLLAMA_CHAT_TIMEOUT", default="300"))
# Arestas com confiança abaixo disto não colam comunidades nem entram no desenho.
CONF_MINIMA = float(config("GRAPH_CONF_MIN", default="0.5"))


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
    if formato == "json_schema":
        # Grammar do Ollama: bloqueia chave ausente e tipo inventado na origem.
        payload["format"] = _SCHEMA_EXTRACAO
    elif formato:
        payload["format"] = formato
    try:
        resposta = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=CHAT_TIMEOUT)
        resposta.raise_for_status()
        return resposta.json()["message"]["content"]
    except (requests.RequestException, KeyError) as erro:
        raise ErroDeGrafo(f"Falha ao chamar o modelo de grafo em {OLLAMA_URL}: {erro}") from erro


# Prompt com um exemplo curto: sem ele o modelo devolve entidades com descricao
# vazia (medido: 0/7 preenchidas sem exemplo, 9/9 com exemplo) e o custo de
# reprocessar a base supera os ~250 tokens do exemplo por chamada.
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
- Nunca crie entidade para caminho de arquivo ou pasta (ex.: docs/, docs/scrum/) nem arquivo de configuracao (ex.: docker-compose.yml).
- Nao crie relacoes cuja origem ou destino seja o nome do produto ou do projeto; eles sao contexto, nao no do grafo.
- Resolva identidades: quando o texto der o usuario/handle e o nome real da mesma entidade (ex.: '@jkatayama' e 'Jessica Katayama'), cite APENAS o nome real, no singular, uma unica vez.

EXEMPLO DE SAIDA ESPERADA:
Texto: "Na Sprint 1, Joao Paulo desenvolveu o modulo de login."
{"entidades":[{"nome":"Sprint 1","tipo":"sprint","descricao":"Primeiro ciclo do projeto"},{"nome":"Joao Paulo","tipo":"pessoa","descricao":"Desenvolvedor"},{"nome":"modulo de login","tipo":"sistema","descricao":"Componente de autenticacao"}],"relacoes":[{"origem":"Joao Paulo","destino":"modulo de login","tipo":"implementa","confianca":0.9,"descricao":"Joao Paulo desenvolveu este modulo"},{"origem":"modulo de login","destino":"Sprint 1","tipo":"pertence_a","confianca":0.8,"descricao":"Modulo desenvolvido na primeira sprint"}]}
"""

# Taxonomia fechada: tipo fora da lista vira 'conceito' (evita entidades verbo).
# Tuplas ordenadas, e nao sets: a ordem vai ao JSON Schema como 'enum' e set
# muda de iteração entre processos (PYTHONHASHSEED), mudando a grammar a cada rodada.
_TIPOS_PERMITIDOS = ("artefato", "conceito", "decisao", "indicador", "pessoa",
                     "requisito", "sistema", "sprint")
# Arestas tambem tem taxonomia fechada: sem isto o modelo gravava 'coleta',
# 'processa', 'decide', 'interage_com' e 'versionado' como tipo de relacao.
_TIPOS_RELACAO = ("bloqueia", "decidido_em", "depende_de", "deriva_de", "implementa",
                  "menciona", "pertence_a", "resolve")

# Schema da extração (formato="json_schema" no _chat). Sem 'minLength': com essa
# restrição a decodificação sob grammar despenca (medido: 193s e JSON truncado no
# 7B) — a gramática só garante forma e enum, conteúdo continua checado no código.
_SCHEMA_EXTRACAO = {
    "type": "object",
    "properties": {
        "entidades": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string"},
                    "tipo": {"type": "string", "enum": list(_TIPOS_PERMITIDOS)},
                    "descricao": {"type": "string"},
                },
                "required": ["nome", "tipo", "descricao"],
            },
        },
        "relacoes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "origem": {"type": "string"},
                    "destino": {"type": "string"},
                    "tipo": {"type": "string", "enum": list(_TIPOS_RELACAO)},
                    "confianca": {"type": "number"},
                    "descricao": {"type": "string"},
                },
                "required": ["origem", "destino", "tipo", "confianca", "descricao"],
            },
        },
    },
    "required": ["entidades", "relacoes"],
}
# Lixo clássico do extrator: datas, breadcrumbs, arquivos e placeholders do modelo.
_RX_LIXO = re.compile(r"\.(md|pdf|txt|json|py|ts|tsx)$|^realit\s*#|\bsem_dado\b", re.IGNORECASE)
_RX_DATA = re.compile(r"^\d{1,2}[/\-.]\d{1,2}([/\-.]\d{2,4})?$")
# Verbos conjugados que o modelo às vezes devolve como 'entidade' (heurística pt).
_RX_VERBO = re.compile(r"(ou|iu|aram|iam|ava|ando|endo|ido)$", re.IGNORECASE)
# Caminhos/breadcrumbs ("docs/scrum/") e arquivos de config ("docker-compose.yml").
_RX_CAMINHO = re.compile(r"^[\w.\-]+(/[\w.\-]*)+/?$|^[\w\-]+\.(ya?ml|toml|env|sql|csv|xlsx?)$", re.IGNORECASE)
# Palavras demasiado genericas para virar no.
_NOMES_GENERICOS = {"sistema", "dados", "projeto", "coisa", "item", "parte", "time", "equipe", "empresa", "produto", "documento", "texto", "informacao", "analise", "processo", "api", "node", "endpoint", "indicador", "modulo", "componente", "requisito","ata", "tela", "log", "interface", "escopo", "plataforma", "cronometro", "base", "atuacao", "tooltip",
                    # papéis e substantivos de organização: em qualquer projeto viram hub
                    # sem significado ligado a dezenas de nós (comparado pela chave canônica,
                    # então 'funcionários'/'usuários' caem aqui também)
                    "desenvolvedor", "developer", "dev", "scrum master", "product owner",
                    "funcionario", "usuario", "membro", "cliente", "pessoa", "colaborador",
                    "stakeholder", "participante", "responsavel", "time tecnico"}
# Infinitivos comuns que o modelo devolve como "entidade" — lista explicita para
# nao rejeitar termos validos em ingles que so terminam em -er/-ar (server, parser).
_VERBOS_BLOQUEADOS = {"gerar", "validar", "indexar", "criar", "definir", "usar", "fazer", "tratar", "extrair", "gerenciar", "configurar", "implementar", "registrar", "armazenar", "processar", "retornar", "exibir", "adicionar", "remover", "atualizar", "buscar", "salvar", "enviar", "receber", "executar", "realizar", "analisar", "verificar", "documentar", "notificar"}
# Regra do prompt ("nome no máximo 4 palavras") aplicada com folga: nomes
# próprios legítimos passam de 4 palavras ("Cooperativa de Crédito Vale Norte");
# o teto pega as frases-verbete que o modelo devolve (~7+ palavras).
_MAX_WORDS_NOME = 6


# Partículas e artigos fora da chave: 'Kayan da Matta' e 'kayanmatta' são a mesma
# pessoa, e 'a autenticação' é o mesmo nó de 'autenticação' — mas isso só colapsa
# se as palavras miúdas saírem em qualquer posição. Não afeta o rótulo exibido.
_PARTICULAS = ("o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das", "e")


def _chave_canonica(nome):
    """Forma de referência: minúscula, sem acento, sem pontuação, sem partículas e sem plural óbvio."""
    t = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9\s-]", " ", t)
    palavras = [w for w in t.split() if w not in _PARTICULAS]
    palavras = [w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("us") else w for w in palavras]
    return " ".join(palavras).strip()


def _chave_identidade(nome):
    """Chave que deduplica nós: a forma canônica sem espaços.

    É o que faz 'kayanmatta' e 'Kayan da Matta' virarem o MESMO nó sem nenhum
    dicionário de apelidos — a normalização é estrutural e vale para qualquer
    projeto de terceiro. A forma legível continua viva no campo `nome`.
    """
    return _chave_canonica(nome).replace(" ", "")


def _nome_melhor(novo, atual):
    """Preferência determinística pelo nome legível: com espaço vence o sem espaço.

    Sem isso, quem nasce primeiro manda para sempre no rótulo do painel — e um
    handle de commit ('jopaul0', 'KauanDomingues') apagaria o nome real da pessoa.
    """
    if novo.lower() == atual.lower():
        return False
    return (" " in novo, len(novo)) > (" " in atual, len(atual))


def _eh_lixo(nome):
    """Rejeita o que não deve virar nó: datas, breadcrumbs, verbos, frases e genéricos.

    É o guardião de "dados de valores reais": nó de lixo polui comunidade e
    degrada a resposta do chat na ponta (retrieval recupera o que a ingestão deixou passar).
    """
    n = (nome or "").strip()
    if len(n) < 3 or _RX_LIXO.search(n) or _RX_DATA.match(n):
        return True
    if _RX_CAMINHO.match(n):
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


def extrair_grafo_do_texto(texto, teto=800, num_predict=1500):
    """Pede ao LLM o dicionário {entidades, relacoes} de um trecho. Inválido vira vazio.

    JSON Schema primeiro (a grammar do Ollama trava chave ausente e enum inventado);
    se vier lixo ou o servidor não aceitar o schema, uma única regrava em JSON
    simples pega modelos que "conversam" melhor sem modo restrito.
    Anti-alucinação: resposta fora do formato não gera grafo — preferimos
    lacuna (nada extraído) a dado inventado.
    """
    bruto = _chat(prompt=texto[:teto], system=_PROMPT_EXTRACAO, num_predict=num_predict, formato="json_schema")
    dados = _extrair_json(bruto)
    if not isinstance(dados, dict):
        bruto = _chat(prompt=texto[:teto], system=_PROMPT_EXTRACAO, num_predict=num_predict, formato="json")
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
    chave = _chave_identidade(bruto)
    if not chave or _chave_canonica(bruto) in _NOMES_GENERICOS:
        return None
    tipo_ok = (tipo or "").strip().lower()
    if tipo_ok not in _TIPOS_PERMITIDOS:
        tipo_ok = "conceito"
    ent = Entidade.objects.filter(chave=chave, projeto=projeto).first()
    if ent:
        # Enriquecimento monotônico: a descrição só entra onde ainda há vazio (não
        # sobrescreve o que uma rodada anterior fundamentou), o tipo 'conceito' —
        # dado à entidade que nasceu apenas como ponta de relação — cede lugar ao
        # tipo declarado pelo modelo, e o rótulo troca pelo nome legível quando o
        # nó foi criado a partir de um handle. Um único UPDATE por nó.
        alterados = {}
        nova_descricao = (descricao or "").strip()
        if not ent.descricao and nova_descricao:
            ent.descricao = nova_descricao
            alterados["descricao"] = nova_descricao
        if ent.tipo == "conceito" and tipo_ok != "conceito":
            ent.tipo = tipo_ok
            alterados["tipo"] = tipo_ok
        if _nome_melhor(bruto, ent.nome):
            ent.nome = bruto[:255]
            alterados["nome"] = ent.nome
        if alterados:
            Entidade.objects.filter(pk=ent.pk).update(**alterados)
        return ent
    return Entidade.objects.create(
        nome=bruto[:255], chave=chave, tipo=tipo_ok, descricao=(descricao or "").strip(), projeto=projeto
    )


def ingestir(limite=None, projeto_id=None, lote=1, documento_id=None, reprocessar=False):
    """Extrai entidades/relações de chunks em lotes (batching). Retorna métricas + tempo.

    Latência: o lote agrupa N chunks por chamada ao LLM (menos idas à GPU);
    chunks curtos (<150 chars) são pulados pois raramente rendem grafo.
    Não altera o estado do Documento: o grafo é uma camada sobre conteúdo
    já indexado pela pipeline de RAG (chunking + embeddings).
    Idempotência: deduplicação por chave canônica + get_or_create na tripla
    (origem, destino, tipo) — reingestir o mesmo doc não duplica arestas.
    Incremental: por padrão só processa chunks ainda não marcados; `reprocessar=True`
    força todos (usar após mudanças no filtro/prompt).
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
    if not reprocessar:
        # Indexação incremental: só chunks ainda não processados pelo grafo.
        queryset = queryset.filter(grafo_processado=False)
    chunks = list(queryset[:limite] if limite else queryset)

    # Agrupar em lotes de `lote` chunks para reduzir chamadas ao LLM
    lotes = [chunks[i:i + lote] for i in range(0, len(chunks), lote)]

    t0 = time.perf_counter()
    n_ent = n_rel = 0
    for grupo in lotes:
        texto_junto = "\n\n---\n\n".join(c.conteudo[:1200] for c in grupo)
        # O teto acompanha o tamanho do lote: sem isso, chunks além do primeiro
        # seriam truncados para fora do prompt (lote pago, 1/3 do texto extraído).
        # Com schema + descrições a saída é mais longa que antes: num_predict maior
        # e o timeout do _chat acompanham (senão a chamada morre no meio do JSON).
        dados = extrair_grafo_do_texto(
            texto_junto, teto=800 * len(grupo), num_predict=min(2500, 1000 * len(grupo))
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
                # Auto-criar entidade se o modelo referenciou nome não declarado.
                # Descrição: reaproveita o texto da própria relação (fundamentado no
                # documento, sem frase-modelo inventada). Tipo permanece 'conceito' —
                # chutar 'pessoa' por ter espaço no nome reclassificaria mal "Django
                # REST Framework", "task #13-1", "modulo de login" (medido: 43 nós no
                # projeto AI4PO). Se o modelo declarar o tipo numa próxima rodada,
                # _obter_ou_criar_entidade faz o upgrade.
                descricao_rel = (rel.get("descricao", "") or "").strip()
                o = mapa.get(_chave_identidade(nome_o))
                if not o and nome_o:
                    o = _obter_ou_criar_entidade(nome_o, "conceito", descricao_rel, projeto_ref)
                    if o:
                        mapa[o.chave] = o
                        n_ent += 1
                d = mapa.get(_chave_identidade(nome_d))
                if not d and nome_d:
                    d = _obter_ou_criar_entidade(nome_d, "conceito", descricao_rel, projeto_ref)
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
                # Última linha de defesa da taxonomia (o schema só vale enquanto o
                # servidor o aceita; no caminho de regrava em JSON ele não existe):
                # tipo fora da lista fechada deixa de poluir a aresta e vira 'menciona'.
                tipo_aresta = (rel.get("tipo", "") or "").strip().lower()
                if tipo_aresta not in _TIPOS_RELACAO:
                    tipo_aresta = "menciona"
                obj, criado = Relacao.objects.get_or_create(
                    origem=o, destino=d, tipo=tipo_aresta[:50],
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
            # Marca o lote como processado: próxima rodada pula estes chunks.
            ChunkDoc.objects.filter(id__in=[c.id for c in grupo]).update(grafo_processado=True)
    dur = round(time.perf_counter() - t0, 1)
    return {"chunks_processados": len(chunks), "lotes": len(lotes), "entidades": n_ent, "relacoes": n_rel, "segundos": dur}


_SEM_FILTRO = object()  # sentinel: distingue "todos os projetos" de "sem projeto"


def _montar_networkx(projeto_id=_SEM_FILTRO, conf_minima=CONF_MINIMA):
    """Grafo não-direcionado de Entidade/Relacao para detecção de comunidades.

    Só entram arestas com confiança mínima (senão chute fraco cola temas
    distintos). projeto_id=None agrupa especificamente as entidades sem projeto.
    """
    import networkx as nx

    G = nx.Graph()
    ents = Entidade.objects.all()
    if projeto_id is not _SEM_FILTRO:
        ents = ents.filter(projeto_id=projeto_id)
    ids = set(ents.values_list("id", flat=True))
    for ent in ents:
        G.add_node(ent.id, nome=ent.nome, tipo=ent.tipo)
    for rel in Relacao.objects.filter(confianca__gte=conf_minima):
        if rel.origem_id in ids and rel.destino_id in ids:
            G.add_edge(rel.origem_id, rel.destino_id, tipo=rel.tipo, confianca=rel.confianca)
    return G


def _detectar_uma(G, min_tamanho=4, resolucao=1.0):
    """Louvain com confiança como peso, sem hubs nem isolados; pequenos reagrupados.

    Hubs (grau >= 2x a média — ex.: nome do produto colado em tudo) ficam fora da
    detecção: eles conectam temas distintos e fariam o Louvain fundir comunidades.
    Grupos abaixo de min_tamanho são reencaixados na comunidade vizinha mais
    próxima, em vez de virar micro-comunidade sem sentido.
    """
    from networkx.algorithms.community import louvain_communities

    graus = dict(G.degree())
    if not graus:
        return []
    medio = sum(graus.values()) / len(graus)
    hubs = {n for n, g in graus.items() if g >= max(2 * medio, 10)}
    H = G.subgraph([n for n in G.nodes() if n not in hubs and graus[n] > 0]).copy()
    try:
        coms = [set(c) for c in louvain_communities(H, weight="confianca", resolution=resolucao, seed=42)]
    except Exception:
        coms = [set(H.nodes())]
    grandes = [c for c in coms if len(c) >= min_tamanho]
    for c in [c for c in coms if len(c) < min_tamanho]:
        if not grandes:
            break
        votos = {i: sum(1 for n in c for v in H.neighbors(n) if v in g) for i, g in enumerate(grandes)}
        if votos and max(votos.values()) > 0:
            grandes[max(votos, key=votos.get)] |= c
    return grandes


def _resumo_comunidade(ents, rels_internas):
    """LLM gera título e resumo com contexto real: descrições E relações, não só nomes."""
    nomes = "\n".join(f"- {e.nome} ({e.tipo}): {e.descricao}" for e in ents)
    arestas = "\n".join(f"- {r.origem.nome} --{r.tipo}--> {r.destino.nome}" for r in rels_internas[:20])
    prompt = (
        "Estas entidades formam um tema do conhecimento de um produto de Product Ownership.\n\n"
        f"ENTIDADES:\n{nomes}\n\nRELAÇÕES:\n{arestas}\n\n"
        'Responda APENAS JSON no formato {"titulo": "", "resumo": ""}.\n'
        "titulo: no maximo 8 palavras, especifico do tema (nunca generico como 'RealIT').\n"
        "resumo: 3 a 5 frases sobre o que o grupo define e como se liga ao resto do produto.\n"
        "Nao comece com 'Este grupo'. Nao invente nada que nao esteja nos dados."
    )
    bruto = _chat(prompt=prompt, num_predict=350, temperature=0.2, formato="json")
    dados = _extrair_json(bruto)
    if not isinstance(dados, dict):
        return "", ""
    return (dados.get("titulo", "") or "")[:255], (dados.get("resumo", "") or "")


def detectar_comunidades(min_tamanho=4, pular_resumo=False, projeto_id=None):
    """Agrupa entidades por modularidade (Louvain, confiança como peso) POR PROJETO.

    Regenera do zero (apaga as comunidades do projeto antes): rodar duas vezes
    não acumula. Título/resumo via LLM; se o Ollama cair, a partição vale e o
    resumo fica vazio para preencher numa segunda rodada.
    """
    t0 = time.perf_counter()
    n = 0
    projeto_ids = list(Entidade.objects.values_list("projeto_id", flat=True).distinct())
    if projeto_id is not None:
        projeto_ids = [p for p in projeto_ids if p == projeto_id]
    for proj_id in projeto_ids:
        G = _montar_networkx(projeto_id=proj_id)
        if G.number_of_nodes() == 0:
            continue
        Comunidade.objects.filter(projeto_id=proj_id).delete()
        for grupo in _detectar_uma(G, min_tamanho=min_tamanho):
            ents = list(Entidade.objects.filter(id__in=list(grupo)))
            ids = {e.id for e in ents}
            rels = list(Relacao.objects.filter(
                confianca__gte=CONF_MINIMA, origem_id__in=ids, destino_id__in=ids
            ).select_related("origem", "destino"))
            titulo = resumo = ""
            if not pular_resumo:
                try:
                    titulo, resumo = _resumo_comunidade(ents, rels)
                except ErroDeGrafo:
                    pass  # partição continua válida; resumo vazio
            if not titulo:
                graus = dict(G.subgraph(grupo).degree())
                titulo = max(ents, key=lambda e: graus.get(e.id, 0)).nome[:255]
            com = Comunidade.objects.create(titulo=titulo, resumo=resumo, tamanho=len(ents), projeto_id=proj_id)
            com.membros.set(ents)
            n += 1
    dur = round(time.perf_counter() - t0, 1)
    return {"comunidades": n, "segundos": dur}