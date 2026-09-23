import json
import requests

from decouple import config
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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
        # Converte o corpo da requisição para texto UTF-8
        body = request.body.decode("utf-8")

        # Converte o JSON recebido para um dicionário Python
        data = json.loads(body)

        message = data.get("message")

        if not message:
            return JsonResponse(
                {"error": "A mensagem é obrigatória."},
                status=400
            )

        # Envia a mensagem para o Ollama
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": message
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

    except requests.exceptions.RequestException as error:
        return JsonResponse(
            {
                "error": "Não foi possível conectar ao Ollama.",
                "details": str(error)
            },
            status=500
        )

    except KeyError:
        return JsonResponse(
            {"error": "Resposta inesperada do Ollama."},
            status=500
        )