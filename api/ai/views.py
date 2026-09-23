import json
import requests

from decouple import config
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ai.chat_com_documento import responder_com_documento
from ai.extraction import (
    ArquivoNaoEncontradoError,
    FalhaDeDecodificacaoError,
    FormatoNaoSuportadoError,
    extrair_texto,
)
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
        # Se vier um arquivo junto (multipart/form-data), a mensagem
        # também chega em request.POST em vez de no corpo JSON puro.
        if request.FILES:
            message = request.POST.get("message")
        else:
            body = request.body.decode("utf-8")
            data = json.loads(body)
            message = data.get("message")

        if not message:
            return JsonResponse(
                {"error": "A mensagem é obrigatória."},
                status=400
            )

        prompt_final = message
        caminho_temporario = None

        if request.FILES:
            arquivo = request.FILES.get("arquivo")

            if arquivo is None:
                return JsonResponse(
                    {"error": "Campo 'arquivo' não encontrado no envio."},
                    status=400
                )

            # Salvo em pasta separada (não em uploads/, que é onde os
            # documentos indexados de verdade ficam) e apago no final:
            # aqui é só um repouso temporário pra reaproveitar
            # extrair_texto, sem virar Documento nem ChunkDoc no banco.
            caminho_temporario = default_storage.save(
                f"temp/{arquivo.name}", arquivo
            )

            try:
                texto_doc = extrair_texto(caminho_temporario)
                prompt_final = responder_com_documento(texto_doc, message)
            finally:
                default_storage.delete(caminho_temporario)

        # Envia a mensagem (ou o prompt com contexto do documento) para o Ollama
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

    except FormatoNaoSuportadoError as error:
        return JsonResponse({"error": str(error)}, status=400)

    except (ArquivoNaoEncontradoError, FalhaDeDecodificacaoError) as error:
        return JsonResponse({"error": str(error)}, status=400)

    except FalhaDeEmbeddingError as error:
        return JsonResponse(
            {
                "error": "Não foi possível gerar os embeddings do documento.",
                "details": str(error)
            },
            status=500
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