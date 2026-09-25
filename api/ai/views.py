import json
import requests
from decouple import config
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ai.chat_com_documento import responder_com_base_vetorial
from ai.indexing import FalhaDeEmbeddingError

OLLAMA_URL = config(
    "OLLAMA_URL",
    default="http://host.docker.internal:11434"
)

MODEL = config(
    "OLLAMA_MODEL",
    default="ai4po-model"
)

@csrf_exempt
def chat(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Apenas POST é permitido."},
            status=405
        )

    try:
        body = request.body.decode("utf-8")
        data = json.loads(body)
        
        message = data.get("message")
        projeto_id = data.get("projeto_id") # Opcional: restringe a busca a um projeto específico
        
        if not message:
            return JsonResponse(
                {"error": "A mensagem é obrigatória."},
                status=400
            )

        # 1. Gera o prompt enriquecido com os trechos da base vetorial (RAG)
        prompt_final = responder_com_base_vetorial(message, projeto_id)

        # 2. Envia a mensagem (com o contexto) para o Ollama
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt_final
                    }
                ],
                "stream": False
            },
            timeout=180
        )
        response.raise_for_status()
        ollama_response = response.json()
        
        return JsonResponse({
            "message": ollama_response["message"]["content"]
        })

    except UnicodeDecodeError:
        return JsonResponse(
            {"error": "O corpo da requisição não está em UTF-8."},
            status=400
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "JSON inválido."},
            status=400
        )
    except FalhaDeEmbeddingError as error:
        print("\n[ERRO RAG - EMBEDDING] Falha ao gerar vetor:")
        print(str(error))
        return JsonResponse({"error": "Não foi possível gerar os embeddings da pergunta.", "details": str(error)}, status=500)
    
    except requests.exceptions.RequestException as error:
        print("\n[ERRO RAG - CONEXÃO] Falha ao conectar no Ollama:")
        print(str(error))
        return JsonResponse({"error": "Não foi possível conectar ao Ollama.", "details": str(error)}, status=500)
    
    except Exception as error:
        import traceback
        print("\n[ERRO RAG - DESCONHECIDO] Erro interno no servidor:")
        traceback.print_exc()
        return JsonResponse({"error": "Erro interno.", "details": str(error)}, status=500)