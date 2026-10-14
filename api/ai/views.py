import json
import logging
from datetime import datetime

import requests
from decouple import config
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ai.indexing import FalhaDeEmbeddingError
from ai.retrieval import responder_com_base_vetorial, responder_com_documento
from users.authentication import CookieJWTAuthentication

from .history import carregar_historico
from .models import Conversa, MensagemChat

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


# ==========================================
# DISPATCHER (MAPEAMENTO DE FUNÇÕES)
# ==========================================
def executar_ferramenta(nome_ferramenta, args, message, projeto_id, documento_texto):
    if nome_ferramenta == "buscar_contexto_projetos":
        return responder_com_base_vetorial(
            pergunta=args.get("termo_pesquisa", message),
            projeto_id=projeto_id,
        )

    if nome_ferramenta == "analisar_documento_anexado":
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
class ChatView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]  # necessário p/ filtrar conversas por usuario_po=request.user

    def post(self, request):
        try:
            # request.data já trata JSON e multipart de forma unificada
            message = (request.data.get("message") or "").strip()
            projeto_id = request.data.get("projeto_id") or None
            conversa_id = request.data.get("conversa_id")
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
            conversa = None
            if conversa_id:
                conversa = get_object_or_404(Conversa, pk=conversa_id, usuario_po=request.user)
                # nos turnos seguintes o front pode não reenviar o projeto
                projeto_id = projeto_id or conversa.projeto_id

            # Injeção de Contexto Dinâmico
            data_hora_formatada = datetime.now().strftime("%A, %d/%m/%Y às %H:%M")
            system_msg = {
                "role": "system",
                "content": (
                    f"Contexto do sistema: A data e hora exata agora é {data_hora_formatada}. "
                    "Local: São José dos Campos, SP. "
                    "LEMBRETE CRÍTICO: Responda SEMPRE em texto humano puro. NUNCA imprima JSONs."
                ),
            }

            conteudo_usuario = message
            if documento_texto:
                conteudo_usuario += (
                    "\n\n[ALERTA INTERNO DO SISTEMA: O usuário anexou um arquivo válido nesta mensagem. "
                    "Você DEVE acionar a ferramenta 'analisar_documento_anexado' para ler o conteúdo dele "
                    "antes de responder.]"
                )

            # Memória multi-turno: histórico vem do banco (conversa nova não tem nenhum)
            historico = carregar_historico(conversa) if conversa else []
            messages = [system_msg, *historico, {"role": "user", "content": conteudo_usuario}]

            # Chamada inicial: o agente decide se usa ferramentas
            response_message = _chamar_ollama(messages, com_tools=True)

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
                    # auto_now só atualiza se o campo estiver em update_fields
                    conversa.save(update_fields=["atualizado_em"])

            return JsonResponse({
                "message": resposta_final,
                "conversa_id": conversa.id if conversa else None,
            })

        except Http404:
            raise
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