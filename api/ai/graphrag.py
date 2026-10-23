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
from pgvector.django import CosineDistance

from ai.indexing import FalhaDeEmbeddingError, gerar_embeddings
from ai.models import ChunkDoc, Entidade, Comunidade, Relacao

OLLAMA_URL = config("OLLAMA_URL", default="http://localhost:11434")
# Para extração usamos o modelo base (sem persona), que segue JSON melhor.
# O default acompanha o modelo realmente usado nos testes locais (GRAPH_MODEL no .env).
MODELO_GRAFO = config("GRAPH_MODEL", default="ai4po-model")
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
- Direcao importa: em 'origem --tipo--> destino' a ORIGEM e quem executa a acao. 'Marya implementou o frontend' -> origem 'Marya Vitoria', destino 'frontend'. Nunca inverta uma relacao de pessoa para coisa.
- 'confianca' e um numero de 0 a 1 indicando quao clara e a relacao no texto.
- Max 12 entidades, 15 relacoes.
- Nunca crie entidade para caminho de arquivo ou pasta (ex.: docs/, docs/scrum/) nem arquivo de configuracao (ex.: docker-compose.yml).
- Nao crie relacoes cuja origem ou destino seja o nome do produto ou do projeto; eles sao contexto, nao no do grafo.
- Resolva identidades: quando o texto der o usuario/handle e o nome real da mesma entidade (ex.: '@jkatayama' e 'Jessica Katayama'), cite APENAS o nome real, no singular, uma unica vez.
- Todo identificador de backlog citado no texto (ex.: '#13-2', 'task #4-3', 'PR #37') DEVE virar entidade do tipo requisito, com o numero no nome ('task #13-2'). Esses identificadores sao como a equipe conversa sobre o trabalho; perde-los quebra a pergunta 'o que a task X entregou?'.

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
    # Remove marcação markdown que o modelo copia do texto: sem isso, nós nascem
    # rotulados como 'branch `feature/13-graphrag`' e o rótulo vira lixo no painel.
    # Só crase e asterisco — underscore é parte do nome de código (grafo_processado).
    bruto = re.sub(r"[*`]+", " ", (nome or "")).strip()
    bruto = re.sub(r"\s{2,}", " ", bruto)
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


# ---------------------------------------------------------------------------
# Retrieval no grafo (task #13-3): transforma o grafo em contexto para o chat.
# ---------------------------------------------------------------------------

# Termos com menos letras que isto não discriminam nada: casariam com tudo
# (o 'acao' dentro de 'autenticacao', por exemplo). O piso vem daí.
_TAMANHO_MINIMO_TERMO = 4


def _termos_da_pergunta(pergunta):
    """Termos de busca da pergunta, na mesma forma canônica usada nos nós.

    Zero LLM de propósito: o retrieval está no caminho da resposta ao usuário,
    então cada chamada ao modelo custaria segundos. A normalização compartilhada
    com a ingestão é o que faz 'autenticações' achar o nó 'autenticação'.
    """
    termos = []
    for termo in _chave_canonica(pergunta or "").split():
        if len(termo) >= _TAMANHO_MINIMO_TERMO and termo not in termos:
            termos.append(termo)
    return termos


def _buscar_sementes(termos, entidades, grau):
    """Nós semente por termos inteiros: nome vale mais que descrição.

    Compara por conjunto de tokens (e não por substring) para que 'acao' não
    pesque o nó 'autenticacao'. Empate de pontuação resolve por grau, assim a
    pergunta 'frontend' cai no componente central e não num sinônimo esquecido.
    """
    marcados = []
    for ent in entidades:
        tokens_nome = set(_chave_canonica(ent.nome).split())
        tokens_descricao = set(_chave_canonica(ent.descricao).split())
        pontos = sum(2 for t in termos if t in tokens_nome) + sum(1 for t in termos if t in tokens_descricao)
        if pontos:
            marcados.append((pontos, grau[ent.id], ent.id))
    marcados.sort(reverse=True)
    return [ent_id for _, _, ent_id in marcados]


# Vocabulário de pergunta que pede GENTE na resposta. Não é lista de nomes: são as
# palavras que qualquer cliente usa ("quem é do time?", "quais os integrantes?").
# Sem essa ponte, nenhuma dessas palavras casa com o nome de uma pessoa e o
# retrieval devolve as arestas do hub do projeto no lugar da equipe.
_PALAVRAS_DE_PESSOA = ("quem", "integrante", "membro", "equipe", "time", "pessoa",
                       "responsavel", "autor", "autoria", "desenvolvedor",
                       "participante", "profissional", "funcional")
_MAXIMO_PESSOAS_SEM_NOME = 12
# Quando a pergunta já cita uma entidade, a ponte de intenção entra só como
# reforço pequeno — injetar a equipe inteira empurra a resposta certa para fora
# do teto de relações.
_MAXIMO_PESSOAS_COM_NOME = 3

# Tetos do bloco injetado na conversa. A janela do Ollama é de 4096 tokens e esse
# espaço é dividido com a persona, o histórico e o resultado da busca vetorial:
# contexto de grafo gordo demais faz o modelo responder string vazia.
_LIMITE_CAMINHOS = 12
_LIMITE_NOS = 14
_LIMITE_TEMAS = 2
_LIMITE_CARACTERES = 2600
# Distância de cosseno máxima aceita como "nó relevante" na busca semântica.
_DISTANCIA_MAXIMA_NO = 0.55


def _sementes_por_intencao(termos, entidades, grau, limite=_MAXIMO_PESSOAS_SEM_NOME):
    """Quando a pergunta fala de gente sem citar nome: devolve as pessoas mais ligadas."""
    if not any(termo in _PALAVRAS_DE_PESSOA for termo in termos):
        return []
    pessoas = [ent for ent in entidades if ent.tipo == "pessoa"]
    pessoas.sort(key=lambda ent: (-grau[ent.id], ent.nome.lower()))
    return [ent.id for ent in pessoas[:limite]]


def _sementes_semanticas(pergunta, projeto_id, ja_escolhidas, limite=3):
    """Vizinhos semânticos da pergunta entre os nós do projeto.

    É o que pega sinônimo que nenhuma regra léxica alcança ('integrantes' ~
    'pessoas do time'). Depende de `graphrag_embeddings` ter rodado; sem vetor
    no banco, ou com o Ollama de embeddings fora do ar, devolve vazio e o
    retrieval segue funcionando só com o caminho léxico.
    """
    if not Entidade.objects.filter(projeto_id=projeto_id, embedding__isnull=False).exists():
        return []  # sem nós vetorizados não há o que comparar: nem chama o serviço
    try:
        vetores = gerar_embeddings([pergunta[:900]])
    except FalhaDeEmbeddingError:
        return []
    if not vetores:
        return []
    proximos = (Entidade.objects
                .filter(projeto_id=projeto_id, embedding__isnull=False)
                .exclude(id__in=ja_escolhidas)
                .annotate(distancia=CosineDistance("embedding", vetores[0]))
                .order_by("distancia")[:limite])
    return [ent.id for ent in proximos if ent.distancia <= _DISTANCIA_MAXIMA_NO]


def buscar_no_grafo(pergunta, projeto_id, max_entidades=5, max_saltos=1):
    """Monta o contexto do grafo (caminhos + comunidades + fontes) para o chat.

    Escopo obrigatório por projeto: sem ele a resposta de um cliente poderia
    citar o grafo de outro. A expansão respeita CONF_MINIMA — a mesma régua do
    desenho e das comunidades — para chute fraco não colar temas distintos.
    Retorna texto puro porque quem consome isto é o agente do Ollama.
    """
    if not projeto_id:
        return ("Nenhuma pergunta ao grafo foi feita sem projeto selecionado: "
                "o conhecimento é organizado por projeto.")
    termos = _termos_da_pergunta(pergunta)
    if not termos:
        return "A pergunta não trouxe termos suficientes para consultar o grafo."

    entidades = list(Entidade.objects.filter(projeto_id=projeto_id))
    if not entidades:
        return "Este projeto ainda não tem grafo de conhecimento: envie e indexe documentos primeiro."
    por_id = {ent.id: ent for ent in entidades}

    arestas = list(Relacao.objects.filter(projeto_id=projeto_id, confianca__gte=CONF_MINIMA)
                   .select_related("origem", "destino")
                   .prefetch_related("evidencias__documento"))
    grau = defaultdict(int)
    vizinhanca = defaultdict(list)
    for aresta in arestas:
        grau[aresta.origem_id] += 1
        grau[aresta.destino_id] += 1
        vizinhanca[aresta.origem_id].append(aresta)
        vizinhanca[aresta.destino_id].append(aresta)

    lexical = _buscar_sementes(termos, entidades, grau)
    sementes = lexical[:max_entidades]
    # Ponte de intenção é FALLBACK: sem nenhuma semente ela traz a equipe inteira;
    # com semente, reforça com poucas pessoas. Injetar 12 pessoas numa pergunta que
    # já cita "GraphRAG" enchia as vagas com arestas de confiança 1.0 e expulsava
    # a resposta certa.
    limite_intencao = _MAXIMO_PESSOAS_SEM_NOME if not sementes else _MAXIMO_PESSOAS_COM_NOME
    for ent_id in _sementes_por_intencao(termos, entidades, grau, limite=limite_intencao):
        if ent_id not in sementes:
            sementes.append(ent_id)
    # Ponte semântica: pega sinônimo que a regra léxica não alcança. Sem nós
    # vetorizados no banco, devolve vazio e o resto continua igual.
    semanticas = _sementes_semanticas(pergunta, projeto_id, set(sementes))
    sementes += semanticas
    # Nós que a pergunta de fato citou: as arestas deles vêm antes das demais.
    relevantes = set(lexical[:max_entidades]) | set(semanticas)
    if not sementes:
        return ("Nenhuma entidade do grafo deste projeto corresponde à pergunta. "
                "Tente outro termo ou consulte os documentos indexados.")

    # BFS de até `max_saltos` a partir das sementes: é o que responde pergunta
    # multi-salto ('quem fez o frontend?' liga pessoa -> frontend -> projeto).
    selecionados = set(sementes)
    bordas = {}
    fronteira = list(sementes)
    for _ in range(max(0, max_saltos)):
        proxima = []
        for ent_id in fronteira:
            for aresta in vizinhanca[ent_id]:
                bordas[aresta.id] = aresta
                outro = aresta.destino_id if aresta.origem_id == ent_id else aresta.origem_id
                if outro not in selecionados:
                    selecionados.add(outro)
                    proxima.append(outro)
        fronteira = proxima

    # Ordem das relações: primeiro as que tocam o nó citado pela pergunta, depois
    # a confiança. Sozinha, a confiança não basta — uma aresta 1,0 de outra pessoa
    # venceria a 0,9 que responde ao que foi perguntado.
    def prioridade(aresta):
        direta = aresta.origem_id in relevantes or aresta.destino_id in relevantes
        return (0 if direta else 1, -aresta.confianca, aresta.id)

    caminhos = [
        f"- {a.origem.nome} --{a.tipo}--> {a.destino.nome} (confiança {a.confianca:.1f})"
        for a in sorted(bordas.values(), key=prioridade)
    ][:_LIMITE_CAMINHOS]
    # Nós na ordem da resposta: semente primeiro, depois por conexão.
    ordem = {ent_id: i for i, ent_id in enumerate(sementes)}
    nos = [
        f"- {por_id[ent_id].nome} ({por_id[ent_id].tipo}): {por_id[ent_id].descricao}"
        for ent_id in sorted(selecionados,
                             key=lambda i: (ordem.get(i, len(sementes)), -grau[i], por_id[i].nome.lower()))
        if por_id[ent_id].descricao
    ][:_LIMITE_NOS]

    comunidades = (Comunidade.objects.filter(projeto_id=projeto_id, membros__id__in=selecionados)
                   .exclude(resumo="").distinct())
    temas = [f"- {c.titulo}: {c.resumo}" for c in comunidades][:_LIMITE_TEMAS]

    # Fontes: documentos dos chunks que sustentam as arestas exibidas. Sem isto,
    # a citação de fontes da #13 oficial não tem de onde sair.
    documentos = sorted({
        chunk.documento.nome
        for aresta in bordas.values()
        for chunk in aresta.evidencias.select_related("documento").all()
    })

    def renderizar(caminhos_, nos_, temas_, documentos_):
        blocos = ["CONHECIMENTO RELACIONADO (grafo do projeto)"]
        if caminhos_:
            blocos.append("Relações:\n" + "\n".join(caminhos_))
        if nos_:
            blocos.append("Entidades:\n" + "\n".join(nos_))
        if temas_:
            blocos.append("Temas do grafo:\n" + "\n".join(temas_))
        if documentos_:
            blocos.append("Fontes: " + ", ".join(documentos_))
        return "\n\n".join(blocos)

    texto = renderizar(caminhos, nos, temas, documentos)
    # Trava final: se ainda estourou o teto, sacrifica na ordem do que menos custa
    # — temas, depois relações, depois nós. Contexto acima da janela do modelo faz
    # ele devolver resposta vazia.
    while len(texto) > _LIMITE_CARACTERES and (temas or caminhos or nos):
        if temas:
            temas = temas[:-1]
        elif caminhos:
            caminhos = caminhos[:-1]
        else:
            nos = nos[:-1]
        texto = renderizar(caminhos, nos, temas, documentos)
    return texto


def embeddar_entidades(projeto_id=None, lote=64):
    """Preenche o vetor dos nós para liberar a busca semântica do retrieval.

    Idempotente: só pega entidade ainda sem embedding, então roda depois da
    ingestão (nó novo nasce sem vetor). Usa o modelo de embeddings pequeno
    (nomic-embed-text), não o 7B — o custo é uma chamada por lote.
    """
    alvo = Entidade.objects.filter(embedding__isnull=True)
    if projeto_id:
        alvo = alvo.filter(projeto_id=projeto_id)
    pendentes = list(alvo.order_by("id"))
    t0 = time.perf_counter()
    total = 0
    for inicio in range(0, len(pendentes), lote):
        grupo = pendentes[inicio:inicio + lote]
        textos = [f"{ent.nome} ({ent.tipo}): {ent.descricao}"[:900] for ent in grupo]
        try:
            vetores = gerar_embeddings(textos)
        except FalhaDeEmbeddingError:
            break
        if len(vetores) != len(grupo):
            break  # contagem divergiu: melhor deixar sem vetor do que chutar
        for ent, vetor in zip(grupo, vetores):
            ent.embedding = vetor
        Entidade.objects.bulk_update(grupo, ["embedding"])
        total += len(grupo)
    return {"embeddings": total, "sem_vetor": len(pendentes) - total,
            "segundos": round(time.perf_counter() - t0, 1)}


def _chunks_elegiveis_para_grafo(documento_id):
    """Chunks do documento com conteúdo suficiente para render grafo (>=150 chars)."""
    return (
        ChunkDoc.objects
        .filter(documento_id=documento_id)
        .annotate(_n=Length("conteudo"))
        .filter(_n__gte=150)
    )


def agendar_ingestao_grafo(documento):
    """Cria o registro de progresso e dispara a ingestão do grafo em background.

    Chamado logo após a indexação (embeddings) no upload: o grafo passa a ser
    montado automaticamente, sem o usuário rodar comando, e o frontend acompanha
    o progresso pelo endpoint de status. Retorna o ProgressoGrafo criado.
    """
    import threading
    from django.utils import timezone
    from ai.models import ProgressoGrafo

    total = _chunks_elegiveis_para_grafo(documento.id).filter(grafo_processado=False).count()
    prog = ProgressoGrafo.objects.create(
        documento=documento,
        projeto=documento.projeto,
        total_chunks=total,
        status='concluido' if total == 0 else 'processando',
    )
    if total == 0:
        prog.finalizado_em = timezone.now()
        prog.save(update_fields=['finalizado_em'])
        return prog

    threading.Thread(target=_ingestao_grafo_worker, args=(prog.id,), daemon=True).start()
    return prog


def _ingestao_grafo_worker(progresso_id):
    """Roda a ingestão em lotes, atualizando o progresso a cada lote, em thread."""
    from django.db import connections
    from django.utils import timezone
    from ai.models import ProgressoGrafo

    LOTE = 2  # chunks por chamada ao LLM; também define a granularidade da barra de %
    prog = None
    try:
        prog = ProgressoGrafo.objects.get(pk=progresso_id)
        documento_id = prog.documento_id
        while True:
            resultado = ingestir(documento_id=documento_id, lote=LOTE, limite=LOTE)
            feitos = resultado.get('chunks_processados', 0)
            if not feitos:
                break
            prog.chunks_processados = min(prog.total_chunks, prog.chunks_processados + feitos)
            prog.save(update_fields=['chunks_processados'])
        prog.status = 'concluido'
        prog.finalizado_em = timezone.now()
        prog.save(update_fields=['status', 'finalizado_em'])
    except Exception as exc:  # nunca deixa a thread morrer silenciosa
        if prog is not None:
            try:
                prog.status = 'erro'
                prog.erro = str(exc)[:500]
                prog.finalizado_em = timezone.now()
                prog.save(update_fields=['status', 'erro', 'finalizado_em'])
            except Exception:
                pass
    finally:
        connections.close_all()