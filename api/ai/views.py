import requests
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://ollama:11434"
)

MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3.5:4b"
)


@csrf_exempt
def chat(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Apenas POST é permitido."},
            status=405
        )

    try:
        data = json.loads(request.body)

        message = data.get("message")

        if not message:
            return JsonResponse(
                {"error": "A mensagem é obrigatória."},
                status=400
            )

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
            timeout=120
        )

        response.raise_for_status()

        ollama_response = response.json()

        return JsonResponse({
            "message": ollama_response["message"]["content"]
        })

    except requests.exceptions.RequestException as error:

        return JsonResponse(
            {
                "error": "Não foi possível conectar ao Ollama.",
                "details": str(error)
            },
            status=500
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {"error": "JSON inválido."},
            status=400
        )