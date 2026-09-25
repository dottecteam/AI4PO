import json
import requests
import traceback
from datetime import datetime
from decouple import config
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ai.retrieval import responder_com_base_vetorial, responder_com_documento
from ai.indexing import FalhaDeEmbeddingError

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
@csrf_exempt
def chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Apenas POST é permitido."}, status=405)

    try:
        # -------------------------------------------------------------
        # Identifica o Content-Type da Requisição
        # -------------------------------------------------------------
        if "multipart/form-data" in request.content_type:
            # Usuário enviou um arquivo em anexo
            message = request.POST.get("message", "")
            projeto_id = request.POST.get("projeto_id")
            arquivo = request.FILES.get("arquivo")
            
            documento_texto = ""
            if arquivo:
                try:
                    documento_texto = arquivo.read().decode("utf-8")
                except UnicodeDecodeError:
                    return JsonResponse({"error": "O arquivo enviado não é um formato de texto válido (UTF-8)."}, status=400)
        else:
            # Chat normal apenas com texto
            body = json.loads(request.body.decode("utf-8"))
            message = body.get("message", "")
            projeto_id = body.get("projeto_id")
            documento_texto = body.get("documento_texto", "")

        if not message and not documento_texto:
            return JsonResponse({"error": "A mensagem ou o documento são obrigatórios."}, status=400)

        # --- LOG VISUAL: PERGUNTA DO USUÁRIO ---
        print(f"\n{'='*60}")
        print(f"👤 [PO]: {message}")
        if documento_texto:
            print(f"📎 [ANEXO DETECTADO]: Arquivo lido com sucesso ({len(documento_texto)} caracteres)")
        print(f"{'='*60}")

        # Injeção de Contexto Dinâmico
        agora = datetime.now()
        data_hora_formatada = agora.strftime("%A, %d/%m/%Y às %H:%M")
        system_msg = {
            "role": "system", 
            "content": f"Contexto do sistema: A data e hora exata agora é {data_hora_formatada}. Local: São José dos Campos, SP. LEMBRETE CRÍTICO: Responda SEMPRE em texto humano puro. NUNCA imprima JSONs."
        }
        
        # O pulo do gato: Avisamos a IA que o arquivo chegou no backend
        conteudo_usuario = message
        if documento_texto:
            conteudo_usuario += "\n\n[ALERTA INTERNO DO SISTEMA: O usuário anexou um arquivo válido nesta mensagem. Você DEVE acionar a ferramenta 'analisar_documento_anexado' para ler o conteúdo dele antes de responder.]"

        messages = [system_msg, {"role": "user", "content": conteudo_usuario}]

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
                
                print(f"⚙️  [AGENTE TOMA DECISÃO]: Acionou a ferramenta '{function_name}' com os argumentos: {args}")
                
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

            # Agente lê os resultados e formula a resposta final
            final_response = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": MODEL, "messages": messages, "stream": False},
                timeout=180
            )
            final_response.raise_for_status()
            resposta_final = final_response.json()["message"]["content"]
            
            # --- LOG VISUAL: RESPOSTA FINAL DO AGENTE ---
            print(f"\n🤖 [AIPO RESPOSTA FINAL]:\n{resposta_final}")
            print(f"{'='*60}\n")
            
            return JsonResponse({"message": resposta_final})

        # Caso ele não utilize ferramentas (Bate-papo)
        resposta_direta = response_message.get("content", "")
        
        # Filtro de Segurança
        if resposta_direta.strip().startswith('{"name":') or resposta_direta.strip().startswith('{"'):
            print(f"⚠️ [WARNING]: Alucinação JSON bloqueada pelo backend.")
            resposta_direta = "Desculpe, acabei me confundindo com a formatação interna. Como posso ajudar você hoje?"

        print(f"🤖 [AIPO BATE-PAPO DIRETO]:\n{resposta_direta}")
        print(f"{'='*60}\n")
        
        return JsonResponse({"message": resposta_direta})

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido."}, status=400)
    except FalhaDeEmbeddingError as error:
        print(f"\n[ERRO RAG] Falha ao gerar vetor: {str(error)}")
        return JsonResponse({"error": "Falha na geração de embeddings.", "details": str(error)}, status=500)
    except Exception as error:
        print(f"\n❌ [ERRO FATAL NO SERVIDOR]")
        traceback.print_exc()
        return JsonResponse({"error": "Erro interno no servidor.", "details": str(error)}, status=500)