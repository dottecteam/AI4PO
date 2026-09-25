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
        return "Nenhum texto de documento foi fornecido nesta requisição."
        
    return f"Erro: Ferramenta '{nome_ferramenta}' não existe."

# ==========================================
# VIEW PRINCIPAL (AGENTIC LOOP)
# ==========================================
@csrf_exempt
def chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Apenas POST é permitido."}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        message = body.get("message", "")
        projeto_id = body.get("projeto_id")
        documento_texto = body.get("documento_texto")

        if not message:
            return JsonResponse({"error": "A mensagem é obrigatória."}, status=400)

        print(f"\n{'='*60}")
        print(f"👤 [PO]: {message}")
        print(f"{'='*60}")

        # -------------------------------------------------------------
        # Injeção de Contexto Dinâmico (Tempo, Local e Trava JSON)
        # -------------------------------------------------------------
        agora = datetime.now()
        data_hora_formatada = agora.strftime("%A, %d/%m/%Y às %H:%M")
        
        system_msg = {
            "role": "system", 
            "content": f"Contexto atual do sistema: A data e hora exata agora é {data_hora_formatada}. Local: São José dos Campos, SP. LEMBRETE CRÍTICO: Responda ao usuário SEMPRE em texto humano puro. NUNCA imprima JSONs na resposta."
        }

        messages = [system_msg, {"role": "user", "content": message}]

        # Chamada inicial
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": MODEL, "messages": messages, "tools": TOOLS, "stream": False},
            timeout=180
        )
        response.raise_for_status()
        response_message = response.json().get("message", {})

        # Execução de Ferramentas
        if response_message.get("tool_calls"):
            # O modelo chamou uma ferramenta DE VERDADE (formato correto da API)
            messages.append(response_message)
            
            for tool_call in response_message["tool_calls"]:
                function_name = tool_call["function"]["name"]
                args = tool_call["function"]["arguments"]
                
                print(f"⚙️  [AGENTE]: Acionou -> {function_name}")
                
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

            # Resposta final após leitura das ferramentas
            final_response = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": MODEL, "messages": messages, "stream": False},
                timeout=180
            )
            final_response.raise_for_status()
            resposta_final = final_response.json()["message"]["content"]
            
            print(f"\n🤖 [AIPO]: {resposta_final}")
            print(f"{'='*60}\n")
            
            return JsonResponse({"message": resposta_final})

        # --- LOG: RESPOSTA DO AGENTE (Sem ferramentas) ---
        resposta_direta = response_message.get("content", "")
        
        if resposta_direta.strip().startswith('{"name":') or resposta_direta.strip().startswith('{"'):
            print(f"⚠️ [WARNING]: O modelo alucinou um JSON na resposta direta. Interceptado.")
            resposta_direta = "Desculpe, eu acabei me confundindo com os formatos internos de ferramentas. Como posso ajudar com os seus projetos hoje?"

        print(f"🤖 [AIPO] (Conversa Direta): {resposta_direta}")
        print(f"{'='*60}\n")
        
        return JsonResponse({"message": resposta_direta})

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido."}, status=400)
    except FalhaDeEmbeddingError as error:
        print("\n[ERRO RAG] Falha ao gerar vetor:", str(error))
        return JsonResponse({"error": "Falha na geração de embeddings.", "details": str(error)}, status=500)
    except Exception as error:
        print("\n[ERRO FATAL]")
        traceback.print_exc()
        return JsonResponse({"error": "Erro interno no servidor.", "details": str(error)}, status=500)