import traceback
import requests
from decouple import config
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from users.authentication import CookieJWTAuthentication
from .prompts import montar_system_prompt

OLLAMA_URL = config("OLLAMA_URL", default="http://host.docker.internal:11434")
MODEL = config("OLLAMA_MODEL", default="llama3.2:3b")

TIPOS_VALIDOS = {"pbi", "feature", "epico"}


class ReformatarRequisitoView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            requisito = (request.data.get("requisito") or "").strip()
            tipo = (request.data.get("tipo") or "pbi").strip().lower()

            if not requisito:
                return JsonResponse({"error": "O campo 'requisito' é obrigatório."}, status=400)

            if tipo not in TIPOS_VALIDOS:
                return JsonResponse(
                    {"error": f"'tipo' inválido. Use um de: {', '.join(sorted(TIPOS_VALIDOS))}."},
                    status=400,
                )

            instrucao = (
                "Responda SOMENTE com a estrutura pedida no system prompt, sem introdução, "
                "sem comentários antes ou depois, sem repetir o rascunho original e sem "
                "reutilizar os nomes/títulos de exemplo citados nas regras — eles são só "
                "formato, o conteúdo tem que vir do rascunho abaixo.\n\n"
                "--- RASCUNHO ---\n"
                f"{requisito}\n"
                "--- FIM DO RASCUNHO ---"
            )

            messages = [
                {"role": "system", "content": montar_system_prompt(tipo)},
                {"role": "user", "content": instrucao},
            ]

            response = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
                timeout=180,
            )
            response.raise_for_status()
            requisito_reformatado = response.json().get("message", {}).get("content", "").strip()

            if not requisito_reformatado:
                return JsonResponse(
                    {"error": "O modelo não retornou nenhum conteúdo."}, status=502
                )

            if requisito_reformatado.startswith('{"name":') or requisito_reformatado.startswith('{"'):
                return JsonResponse(
                    {"error": "O modelo retornou um formato inesperado. Tente novamente."},
                    status=502,
                )

            return JsonResponse({
                "tipo": tipo,
                "requisito_original": requisito,
                "requisito_reformatado": requisito_reformatado,
            })

        except requests.exceptions.RequestException as error:
            traceback.print_exc()
            return JsonResponse(
                {"error": "Falha ao comunicar com o serviço de IA.", "details": str(error)},
                status=502,
            )
        except Exception as error:
            traceback.print_exc()
            return JsonResponse(
                {"error": "Erro interno no servidor.", "details": str(error)}, status=500
            )