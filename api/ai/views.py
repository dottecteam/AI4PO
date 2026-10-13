import requests
import traceback
from datetime import datetime
from decouple import config
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ai.retrieval import responder_com_base_vetorial, responder_com_documento
from ai.indexing import FalhaDeEmbeddingError
from .history import carregar_historico
from .models import Conversa, MensagemChat
from .titulo import gerar_titulo

OLLAMA_URL = config("OLLAMA_URL", default="http://host.docker.internal:11434")
MODEL = config("OLLAMA_MODEL", default="llama3.2:3b")

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
                "required": ["termo_pesquisa"]
            }
        }
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
                "required": ["pergunta"]
            }
        }
    }
]

# ==========================================
# DISPATCHER (MAPEAMENTO DE FUNÇÕES)
# ==========================================
def executar_ferramenta(nome_ferramenta, args, message, projeto_id, documento_texto):
    if nome_ferramenta == "buscar_contexto_projetos":
        return responder_com_base_vetorial(
            pergunta=args.get("termo_pesquisa", message),
            projeto_id=projeto_id
        )

    elif nome_ferramenta == "analisar_documento_anexado":
        if documento_texto:
            return responder_com_documento(texto_doc=documento_texto, pergunta=args.get("pergunta", message))
        return "Nenhum documento foi anexado a esta requisição."

    return f"Erro: Ferramenta '{nome_ferramenta}' não existe."


# ==========================================
# VIEW PRINCIPAL (AGENTIC LOOP)
# ==========================================
from users.authentication import CookieJWTAuthentication

class ChatView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]  # necessário p/ filtrar conversas por usuario_po=request.user

    def post(self, request):
        try:
            # request.data já trata JSON e multipart de forma unificada
            message = request.data.get("message", "")
            projeto_id = request.data.get("projeto_id")
            conversa_id = request.data.get("conversa_id")
            nova_conversa = not conversa_id  # só gera título na primeira troca
            arquivo = request.FILES.get("arquivo")

            documento_texto = ""
            anexo_nome = ""
            if arquivo:
                anexo_nome = arquivo.name
                try:
                    documento_texto = arquivo.read().decode("utf-8")
                except UnicodeDecodeError:
                    return JsonResponse({"error": "O arquivo enviado não é um formato de texto válido (UTF-8)."}, status=400)
            elif not arquivo:
                documento_texto = request.data.get("documento_texto", "")

            if not message and not documento_texto:
                return JsonResponse({"error": "A mensagem ou o documento são obrigatórios."}, status=400)

            # pergunta do usuário
            print(f"\n{'='*60}")
            print(f"👤 [PO]: {message}")
            if documento_texto:
                print(f"📎 [ANEXO DETECTADO]: Arquivo lido com sucesso ({len(documento_texto)} caracteres)")
            print(f"{'='*60}")

            # Busca ou cria a conversa, com ligação ao usuário logado
            if conversa_id:
                conversa = get_object_or_404(Conversa, pk=conversa_id, usuario_po=request.user)
            else:
                conversa = Conversa.objects.create(
                    usuario_po=request.user,
                    projeto_id=projeto_id or None,
                    titulo=(message[:60] if message else "Nova conversa"),
                )

            # Injeção de Contexto Dinâmico
            agora = datetime.now()
            data_hora_formatada = agora.strftime("%A, %d/%m/%Y às %H:%M")
            system_msg = {
                "role": "system",
                "content": f"Contexto do sistema: A data e hora exata agora é {data_hora_formatada}. Local: São José dos Campos, SP. LEMBRETE CRÍTICO: Responda SEMPRE em texto humano puro. NUNCA imprima JSONs."
            }

            conteudo_usuario = message
            if documento_texto:
                conteudo_usuario += "\n\n[ALERTA INTERNO DO SISTEMA: O usuário anexou um arquivo válido nesta mensagem. Você DEVE acionar a ferramenta 'analisar_documento_anexado' para ler o conteúdo dele antes de responder.]"

            # histórico vem do banco
            historico = carregar_historico(conversa)
            messages = [system_msg, *historico, {"role": "user", "content": conteudo_usuario}]

            # Chamada inicial para o Agente decidir o que fazer
            response = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": MODEL, "messages": messages, "tools": TOOLS, "stream": False},
                timeout=180
            )
            response.raise_for_status()
            response_message = response.json().get("message", {})

            # Execução de Ferramentas
            if response_message.get("tool_calls"):
                messages.append(response_message)

                for tool_call in response_message["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    args = tool_call["function"]["arguments"]

                    print(f" [AGENTE TOMA DECISÃO]: Acionou a ferramenta '{function_name}' com os argumentos: {args}")

                    resultado_ferramenta = executar_ferramenta(
                        nome_ferramenta=function_name,
                        args=args,
                        message=message,
                        projeto_id=projeto_id,
                        documento_texto=documento_texto
                    )

                    messages.append({
                        "role": "tool",
                        "content": str(resultado_ferramenta),
                        "name": function_name
                    })

                final_response = requests.post(
                    f"{OLLAMA_URL}/api/chat",
                    json={"model": MODEL, "messages": messages, "stream": False},
                    timeout=180
                )
                final_response.raise_for_status()
                resposta_final = final_response.json()["message"]["content"]

                print(f"\n [AIPO RESPOSTA FINAL]:\n{resposta_final}")
                print(f"{'='*60}\n")

            else:
                # Caso ele não utilize ferramentas (Bate-papo)
                resposta_final = response_message.get("content") or ""

                # Filtro de Segurança
                if resposta_final.strip().startswith('{"name":') or resposta_final.strip().startswith('{"'):
                    print(f" [WARNING]: Alucinação JSON bloqueada pelo backend.")
                    resposta_final = "Desculpe, acabei me confundindo com a formatação interna. Como posso ajudar você hoje?"

                print(f" [AIPO BATE-PAPO DIRETO]:\n{resposta_final}")
                print(f"{'='*60}\n")

            # Salva o par pergunta/resposta de uma vez — assim não fica pergunta
            # sem resposta no histórico se o Ollama der timeout antes disso.
            MensagemChat.objects.bulk_create([
                MensagemChat(conversa=conversa, papel="user", conteudo=message, anexo_nome=anexo_nome),
                MensagemChat(conversa=conversa, papel="assistant", conteudo=resposta_final),
            ])

            # na primeira troca, pede ao Ollama um título curto.
            # Se falhar, fica o título provisório (primeiros 60 caracteres da pergunta).
            if nova_conversa and message:
                titulo = gerar_titulo(message, resposta_final)
                if titulo:
                    conversa.titulo = titulo

            conversa.save()  # auto_now atualiza atualizado_em, pra conversa subir na sidebar

            return JsonResponse({"message": resposta_final, "conversa_id": conversa.id})

        except Http404:
            raise
        except Exception as error:
            if isinstance(error, FalhaDeEmbeddingError):
                print(f"\n[ERRO RAG] Falha ao gerar vetor: {str(error)}")
                return JsonResponse({"error": "Falha na geração de embeddings.", "details": str(error)}, status=500)
            print(f"\n [ERRO FATAL NO SERVIDOR]")
            traceback.print_exc()
            return JsonResponse({"error": "Erro interno no servidor.", "details": str(error)}, status=500)