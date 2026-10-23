import json
import logging
import threading
from datetime import datetime
import re

import requests
from decouple import config
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai import similarity
from ai.graphrag import buscar_no_grafo
from ai.indexing import FalhaDeEmbeddingError
from ai.retrieval import (
    _formatar_contexto,
    buscar_trechos,
    responder_com_base_vetorial,
    responder_com_documento,
)
from users.authentication import CookieJWTAuthentication

from .history import carregar_historico
from .models import Conversa, MensagemChat
from .titulo import gerar_titulo
from .validacao_chat import (
    MENSAGEM_SEM_MODELO,
    detectar_especificacao,
    montar_validacao,
    para_markdown,
    resumo_curto,
)
from .summary import atualizar_resumo
from .reformatar import (
    ReformatacaoError,
    classificar_intencao,
    gerar_reformatacao,
    reformatacao_pendente,
    salvar_reformatacao,
)

from .reformatar import TIPOS_VALIDOS

logger = logging.getLogger(__name__)

OLLAMA_URL = config("OLLAMA_URL", default="http://host.docker.internal:11434")
MODEL = config("OLLAMA_MODEL", default="llama3.2:3b")
# Janela de contexto pedida ao Ollama: precisa caber system + tools + histórico + RAG.
NUM_CTX = config("OLLAMA_NUM_CTX", default=8192, cast=int)
OLLAMA_TIMEOUT = 180
MAX_ARQUIVO_BYTES = 2 * 1024 * 1024  # 2 MB de texto já é muito para o chat

MSG_FALLBACK = "Desculpe, acabei me confundindo com a formatação interna. Como posso ajudar você hoje?"
MSG_VAZIA = "Não consegui gerar uma resposta para essa pergunta. Tente reformulá-la ou dividi-la em partes menores."

# Reaproveita a conexão TCP com o Ollama entre as chamadas (pedido -> ferramenta -> resposta).
_http = requests.Session()

# ==========================================
# DEFINIÇÃO DAS FERRAMENTAS (SKILLS)
# ==========================================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_contexto_projetos",
            "description": "Busca no banco de dados histórico, regras e dados técnicos de projetos. Acione APENAS para dúvidas técnicas, de negócio ou gestão.",
            "parameters": {
                "type": "object",
                "properties": {
                    "termo_pesquisa": {"type": "string", "description": "Palavra-chave curta para a busca."}
                },
                "required": ["termo_pesquisa"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            # Task #13-3: o grafo responde o que a busca vetorial não alcança —
            # relacionamento entre pessoas, requisitos e decisões.
            "name": "consultar_grafo_conhecimento",
            "description": (
                "Consulta o GRAFO de conhecimento do projeto: quem fez ou é dono de quê, o que "
                "depende de quê, o que foi decidido e em qual sprint, e como os temas se agrupam. "
                "Acione para perguntas de RELACIONAMENTO (pessoa -> entrega, requisito -> decisão). "
                "Para conteúdo literal de um documento, prefira buscar_contexto_projetos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pergunta": {"type": "string", "description": "A pergunta do usuário, integral."}
                },
                "required": ["pergunta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analisar_documento_anexado",
            "description": "Extrai informações de um texto que o usuário acabou de enviar no chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pergunta": {"type": "string", "description": "Dúvida do usuário sobre o documento."}
                },
                "required": ["pergunta"],
            },
        },
    },
]


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================
def _chamar_ollama(messages, com_tools=False):
    """Uma chamada ao /api/chat do Ollama; devolve o dict `message` da resposta."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"num_ctx": NUM_CTX},
    }
    if com_tools:
        payload["tools"] = TOOLS

    resposta = _http.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=OLLAMA_TIMEOUT)
    resposta.raise_for_status()
    dados = resposta.json()
    mensagem = dados.get("message", {})
    if not (mensagem.get("content") or "").strip() and not mensagem.get("tool_calls"):
        # diagnóstico: motivo da parada e tamanho real do prompt processado
        logger.warning(
            "Ollama devolveu conteúdo vazio: done_reason=%s prompt_tokens=%s resposta_tokens=%s",
            dados.get("done_reason"), dados.get("prompt_eval_count"), dados.get("eval_count"),
        )
    return mensagem


def _normalizar_args(args):
    """O Ollama normalmente devolve dict, mas alguns modelos mandam string JSON."""
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return {}
    return args if isinstance(args, dict) else {}


def _json_vazado(texto):
    """Modelos pequenos às vezes imprimem a chamada de ferramenta como texto."""
    return texto.strip().startswith('{"')


def _ler_anexo(arquivo):
    """Lê o arquivo enviado como UTF-8. Levanta ValueError com mensagem pronta pro usuário."""
    if arquivo.size > MAX_ARQUIVO_BYTES:
        raise ValueError(f"O arquivo excede o limite de {MAX_ARQUIVO_BYTES // (1024 * 1024)} MB.")
    try:
        return arquivo.read().decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("O arquivo enviado não é um formato de texto válido (UTF-8).")


def _mesclar_fontes(fontes, novas):
    """Mescla os trechos de `novas` em `fontes`, sem duplicar por chunk_id."""
    existentes = {f["chunk_id"] for f in fontes}
    for f in novas:
        if f["chunk_id"] not in existentes:
            fontes.append(f)
            existentes.add(f["chunk_id"])


# ==========================================
# DISPATCHER (MAPEAMENTO DE FUNÇÕES)
# ==========================================
def executar_ferramenta(nome_ferramenta, args, message, projeto_id, documento_texto, usuario, fontes):
    if nome_ferramenta == "buscar_contexto_projetos":
        # a busca é restrita aos projetos do usuário; `fontes` recebe a origem dos trechos
        return responder_com_base_vetorial(
            pergunta=args.get("termo_pesquisa", message),
            usuario=usuario,
            projeto_id=projeto_id,
            fontes=fontes,
        )

    elif nome_ferramenta == "consultar_grafo_conhecimento":
        pergunta = args.get("pergunta", message)

        novas = []
        resposta_docs = responder_com_base_vetorial(
            pergunta=pergunta,
            usuario=usuario,
            projeto_id=projeto_id,
            fontes=novas,
        )
        _mesclar_fontes(fontes, novas)

        resposta_grafo = buscar_no_grafo(
            pergunta=pergunta,
            projeto_id=projeto_id,
        )

        if resposta_grafo and str(resposta_grafo).strip():
            return (
                f"{resposta_docs}\n\n"
                f"Informações do grafo:\n{resposta_grafo}"
            )

        return resposta_docs

    elif nome_ferramenta == "analisar_documento_anexado":
        if documento_texto:
            return responder_com_documento(
                texto_doc=documento_texto,
                pergunta=args.get("pergunta", message),
            )
        return "Nenhum documento foi anexado a esta requisição."

    return f"Erro: Ferramenta '{nome_ferramenta}' não existe."


# ==========================================
# VIEW PRINCIPAL (AGENTIC LOOP)
# ==========================================
class SimilarityCheckView(APIView):
    def post(self, request):
        texto = (
            request.data.get("texto")
            if isinstance(request.data, dict)
            else None
        )

        if not isinstance(texto, str):
            return Response(
                {"detail": "O campo texto deve ser uma string."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not texto.strip():
            return Response({"resultados": []})

        try:
            resultados = similarity.verificar_similaridade(texto)
        except FalhaDeEmbeddingError:
            return Response(
                {"detail": "Verificação de similaridade indisponível."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "resultados": [
                    {
                        "chunkId": resultado.chunk_id,
                        "conteudo": resultado.conteudo,
                        "similaridade": resultado.similaridade,
                        "projeto": {
                            "id": resultado.projeto_id,
                            "titulo": resultado.projeto_titulo,
                        },
                        "documento": {
                            "id": resultado.documento_id,
                            "nome": resultado.documento_nome,
                        },
                    }
                    for resultado in resultados
                ]
            }
        )
    
_RX_COMANDO_REFORMATAR = re.compile(r"^/reformatar(?:\s+|$)", re.IGNORECASE)
 
 
def _interpretar_comando_reformatar(texto):
    """'/reformatar [pbi|feature|epico] <rascunho>' -> (tipo, rascunho)."""
    corpo = _RX_COMANDO_REFORMATAR.sub("", texto, count=1).strip()
    tipo = "pbi"
    partes = corpo.split(None, 1)
    if partes and partes[0].lower().replace("é", "e") in TIPOS_VALIDOS:
        tipo = partes[0].lower().replace("é", "e")
        corpo = partes[1].strip() if len(partes) > 1 else ""
    return tipo, corpo
 
 
def _aplicar_titulo_gerado(conversa, pergunta, resposta):
    """Pede um título curto ao Ollama e grava na conversa. Devolve True se gravou.
 
    Se a geração falhar, fica o título provisório (primeiros 60 caracteres).
    """
    titulo = gerar_titulo(pergunta, resposta)
    if not titulo:
        return False
    conversa.titulo = titulo[:120]  # titulo tem max_length=120
    # "titulo" precisa estar em update_fields; auto_now só atualiza
    # "atualizado_em" se o campo também estiver na lista
    conversa.save(update_fields=["titulo", "atualizado_em"])
    return True
 
 
class ChatView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]  # necessário p/ filtrar conversas por usuario_po=request.user
 
    def post(self, request):
        try:
            # request.data já trata JSON e multipart de forma unificada
            message = (request.data.get("message") or "").strip()
            projeto_id = request.data.get("projeto_id") or None
            conversa_id = request.data.get("conversa_id")
            nova_conversa = not conversa_id  # só gera título na primeira troca
            arquivo = request.FILES.get("arquivo")
 
            documento_texto = ""
            anexo_nome = ""
            if arquivo:
                anexo_nome = arquivo.name
                try:
                    documento_texto = _ler_anexo(arquivo)
                except ValueError as erro:
                    return JsonResponse({"error": str(erro)}, status=400)
            else:
                documento_texto = request.data.get("documento_texto", "")
 
            if not message and not documento_texto:
                return JsonResponse({"error": "A mensagem ou o documento são obrigatórios."}, status=400)
 
            logger.info("[PO] %s", message)
            if documento_texto:
                logger.info("[ANEXO] %s (%d caracteres)", anexo_nome or "texto colado", len(documento_texto))
 
            # Conversa existente é carregada agora; a nova só é criada ao persistir,
            # assim uma falha do Ollama não deixa conversa vazia na sidebar.
            # ATENÇÃO: em conversa nova, `conversa` continua None até a persistência.
            conversa = None
            if conversa_id:
                conversa = get_object_or_404(Conversa, pk=conversa_id, usuario_po=request.user)
                # nos turnos seguintes o front pode não reenviar o projeto
                projeto_id = projeto_id or conversa.projeto_id
 
            # ==========================================
            # ROTEAMENTO: reformatar / ajustar / conversar
            # ==========================================
            # "/reformatar" é comando explícito: não passa pelo roteador LLM (o modelo
            # pequeno erra a classificação). Os demais comandos (ex.: /validar) também
            # não passam pelo roteador: ele poderia desviar a mensagem para reformatação,
            # pulando a validação determinística abaixo.
            texto = message.strip()
            eh_comando_reformatar = bool(_RX_COMANDO_REFORMATAR.match(texto))
 
            if texto and not documento_texto and (eh_comando_reformatar or not texto.startswith("/")):
                anterior = reformatacao_pendente(conversa) if conversa else None
 
                if eh_comando_reformatar:
                    tipo, rascunho = _interpretar_comando_reformatar(texto)
                    if not rascunho:
                        return JsonResponse(
                            {"error": "Use: /reformatar [pbi|feature|epico] <rascunho do requisito>."},
                            status=400,
                        )
                    message = rascunho  # é o que vai para o histórico, sem o "/reformatar"
                    intencao = "reformatar"
                    anterior = None  # comando explícito sempre gera uma versão nova
                else:
                    intencao, tipo = classificar_intencao(
                        message, ultima_foi_reformatacao=anterior is not None
                    )
                    # "ajustar" só faz sentido logo depois de uma reformatação
                    if intencao == "ajustar" and anterior is None:
                        intencao = "conversar"
 
                print(f" [ROTEADOR]: intenção='{intencao}', tipo='{tipo}'")
 
                if intencao in ("reformatar", "ajustar"):
                    resultado = gerar_reformatacao(
                        message, tipo, anterior if intencao == "ajustar" else None
                    )
 
                    # A conversa nova só é criada depois que o Ollama respondeu
                    with transaction.atomic():
                        if conversa is None:
                            conversa = Conversa.objects.create(
                                usuario_po=request.user,
                                projeto_id=projeto_id,
                                titulo=(message[:60] or "Nova conversa"),
                            )
                        salvar_reformatacao(conversa, message, resultado)
 
                    # Conversa nova: troca o título provisório por um título gerado
                    if nova_conversa:
                        _aplicar_titulo_gerado(conversa, message, resultado["reformatado"])
 
                    print(f"\n [AIPO REFORMATAÇÃO ({resultado['tipo']})]:\n{resultado['reformatado']}")
                    print(f"{'='*60}\n")
 
                    return JsonResponse({
                        "message": resultado["reformatado"],
                        "conversa_id": conversa.id,
                        "reformatacao": {
                            "original": resultado["original"],
                            "tipo": resultado["tipo"],
                        },
                    })
 
            # Injeção de Contexto Dinâmico
            data_hora_formatada = datetime.now().strftime("%A, %d/%m/%Y às %H:%M")
            conteudo_system = (
                f"Contexto do sistema: A data e hora exata agora é {data_hora_formatada}. "
                "Local: São José dos Campos, SP. "
                "IMPORTANTE: para perguntas sobre projetos, documentos, equipe ou decisões, "
                "ACIONE as ferramentas de busca ANTES de responder. A resposta FINAL ao usuário "
                "deve ser em texto corrido (sem JSON) — mas usar ferramentas é permitido e encorajado."
            )
            # Memória de longo prazo: o que já saiu da janela de mensagens vive no resumo
            if conversa and conversa.resumo:
                conteudo_system += (
                    "\n\nResumo da conversa até aqui (mensagens mais antigas, já fora do histórico): "
                    f"{conversa.resumo}"
                )
            system_msg = {"role": "system", "content": conteudo_system}
 
            conteudo_usuario = message
            if documento_texto:
                conteudo_usuario += (
                    "\n\n[ALERTA INTERNO DO SISTEMA: O usuário anexou um arquivo válido nesta mensagem. "
                    "Você DEVE acionar a ferramenta 'analisar_documento_anexado' para ler o conteúdo dele "
                    "antes de responder.]"
                )
 
            # Validação de especificação (task #8-3): determinística, não passa pelo Ollama.
            texto_spec = detectar_especificacao(message, documento_texto)
            if texto_spec is not None:
                validacao = montar_validacao(texto_spec)
                if validacao is None:
                    resposta_md = resposta_curta = MENSAGEM_SEM_MODELO
                else:
                    resposta_md = para_markdown(validacao)
                    resposta_curta = resumo_curto(validacao)
 
                with transaction.atomic():
                    if conversa is None:
                        # conversa nova: criada já com o título da validação
                        conversa = Conversa.objects.create(
                            usuario_po=request.user,
                            projeto_id=projeto_id,
                            titulo="Validação de especificação",
                        )
                    elif not conversa.mensagens.exists():
                        conversa.titulo = "Validação de especificação"
 
                    MensagemChat.objects.bulk_create([
                        MensagemChat(
                            conversa=conversa,
                            papel="user",
                            conteudo=message or f"[Anexo: {anexo_nome}]",
                            anexo_nome=anexo_nome,
                        ),
                        MensagemChat(conversa=conversa, papel="assistant", conteudo=resposta_md),
                    ])
                    conversa.save()
 
                return JsonResponse({
                    "message": resposta_curta,
                    "conversa_id": conversa.id,
                    "validacao": validacao,
                })
 
            # Memória multi-turno: histórico vem do banco (conversa nova não tem nenhum)
            historico = carregar_historico(conversa) if conversa else []
            fontes = []  # origem (projeto/documento) dos trechos que a busca trouxe
 
            # Recuperação DETERMINÍSTICA (RAG de documentos + GraphRAG): quando há
            # pergunta textual, a busca SEMPRE roda aqui e o resultado é injetado no
            # prompt. A resposta fica ancorada nos dados do projeto em vez de depender
            # do modelo "decidir" chamar a ferramenta (pular a busca gerava alucinação).
            if message.strip():
                try:
                    contexto_docs = responder_com_base_vetorial(
                        pergunta=message, usuario=request.user,
                        projeto_id=projeto_id, fontes=fontes,
                    )
                except FalhaDeEmbeddingError:
                    logger.warning("Embeddings indisponíveis; seguindo sem contexto vetorial.")
                    contexto_docs = ""
                contexto_grafo = ""
                if projeto_id:
                    try:
                        contexto_grafo = buscar_no_grafo(pergunta=message, projeto_id=projeto_id) or ""
                    except Exception:
                        logger.exception("Falha ao consultar o grafo de conhecimento.")
                        contexto_grafo = ""
                # Só injeta se a relevância for alta: saudações casam com similaridade
                # baixa (~0.58) e não devem puxar contexto; pergunta real sobre o
                # projeto fica em ~0.75+. O corte 0.65 separa bem os dois casos.
                melhor_sim = max((f.get("similaridade", 0.0) for f in fontes), default=0.0)
                relevante = melhor_sim >= 0.65
                if not relevante:
                    fontes = []  # saudação/pergunta solta: nao mostra fontes irrelevantes
                partes = []
                if relevante and contexto_docs.strip():
                    partes.append(contexto_docs)
                if relevante and contexto_grafo.strip():
                    partes.append(contexto_grafo)
                if partes:
                    conteudo_usuario += (
                        "\n\n=== CONTEXTO DOS PROJETOS (documentos + grafo) ===\n"
                        + "\n\n".join(partes)
                        + "\n=== FIM DO CONTEXTO ===\n"
                        "Responda usando SOMENTE esse contexto. Se algo não constar nele, "
                        "diga que não consta no contexto — NÃO invente."
                    )
 
            messages = [system_msg, *historico, {"role": "user", "content": conteudo_usuario}]
 
            # Ferramentas só entram no caso de documento ANEXADO (analisar_documento_anexado).
            # Em pergunta comum o contexto já foi injetado acima, entao nao se passa tools
            # (evita a busca rodar duas vezes e estourar a latencia).
            response_message = _chamar_ollama(messages, com_tools=bool(documento_texto))
            tool_calls = response_message.get("tool_calls")
            if tool_calls:
                messages.append(response_message)
 
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    args = _normalizar_args(tool_call["function"].get("arguments"))
 
                    logger.info("[AGENTE] ferramenta '%s' args=%s", function_name, args)
 
                    resultado = executar_ferramenta(
                        nome_ferramenta=function_name,
                        args=args,
                        message=message,
                        projeto_id=projeto_id,
                        documento_texto=documento_texto,
                        usuario=request.user,
                        fontes=fontes,
                    )
                    # "tool_name" é o campo atual da API do Ollama; "name" fica por compatibilidade
                    messages.append({
                        "role": "tool",
                        "content": str(resultado),
                        "tool_name": function_name,
                        "name": function_name,
                    })
 
                # Segunda chamada, sem tools: o modelo só redige a resposta final
                resposta_final = _chamar_ollama(messages).get("content") or ""
 
                # Modelos pequenos às vezes devolvem vazio logo após o resultado da ferramenta.
                # Uma segunda tentativa com instrução explícita costuma resolver.
                if not resposta_final.strip():
                    logger.warning("Resposta vazia após ferramenta; tentando de novo com instrução explícita.")
                    messages.append({
                        "role": "user",
                        "content": "Com base no contexto retornado acima, responda agora à minha pergunta "
                                   "original em texto corrido, em português.",
                    })
                    resposta_final = _chamar_ollama(messages).get("content") or ""
            else:
                resposta_final = response_message.get("content") or ""
 
            # Filtro de segurança (vale para os dois caminhos) + resposta vazia.
            # O fallback é devolvido ao usuário, mas não vai pro histórico.
            salvar_no_historico = True
            if not resposta_final.strip():
                logger.warning("Modelo devolveu resposta vazia mesmo após nova tentativa.")
                resposta_final = MSG_VAZIA
                salvar_no_historico = False
            elif _json_vazado(resposta_final):
                logger.warning("JSON vazado bloqueado: %r", resposta_final[:200])
                resposta_final = MSG_FALLBACK
                salvar_no_historico = False
 
            logger.info("[AIPO] %s", resposta_final)
 
            if salvar_no_historico:
                # Persistência atômica: nunca fica pergunta sem resposta no histórico
                with transaction.atomic():
                    if conversa is None:
                        conversa = Conversa.objects.create(
                            usuario_po=request.user,
                            projeto_id=projeto_id,
                            titulo=(message[:60] or anexo_nome or "Nova conversa"),
                        )
                    MensagemChat.objects.bulk_create([
                        MensagemChat(
                            conversa=conversa,
                            papel="user",
                            conteudo=message or f"[Anexo: {anexo_nome}]",
                            anexo_nome=anexo_nome,
                        ),
                        MensagemChat(conversa=conversa, papel="assistant", conteudo=resposta_final),
                    ])
 
            # na primeira troca, pede ao Ollama um título curto.
            # Se falhar, fica o título provisório (primeiros 60 caracteres da pergunta).
            # `conversa` pode ser None se a resposta foi o fallback e nada foi persistido.
            if nova_conversa and message and conversa:
                if _aplicar_titulo_gerado(conversa, message, resposta_final):
                    # Resumo em segundo plano, só depois do commit: não atrasa a resposta
                    transaction.on_commit(
                        lambda cid=conversa.id: threading.Thread(
                            target=atualizar_resumo, args=(cid,), daemon=True
                        ).start()
                    )
 
            return JsonResponse({
                "message": resposta_final,
                "conversa_id": conversa.id if conversa else None,
                "fontes": fontes,
            })
 
        except Http404:
            raise
        except ReformatacaoError as erro:
            return JsonResponse({"error": erro.mensagem}, status=erro.status)
        except requests.Timeout:
            logger.error("Timeout ao chamar o Ollama")
            return JsonResponse({"error": "O modelo demorou demais para responder. Tente novamente."}, status=504)
        except requests.ConnectionError:
            logger.error("Ollama inacessível em %s", OLLAMA_URL)
            return JsonResponse({"error": "Serviço de IA indisponível no momento."}, status=503)
        except FalhaDeEmbeddingError as erro:
            logger.error("Falha ao gerar vetor: %s", erro)
            return JsonResponse({"error": "Falha na geração de embeddings.", "details": str(erro)}, status=500)
        except Exception as erro:
            logger.exception("Erro fatal no ChatView")
            return JsonResponse({"error": "Erro interno no servidor.", "details": str(erro)}, status=500)
