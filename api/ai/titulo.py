import re

import requests
from decouple import config

OLLAMA_URL = config("OLLAMA_URL", default="http://host.docker.internal:11434")
MODEL = config("OLLAMA_MODEL", default="llama3.2:3b")


def gerar_titulo(pergunta: str, resposta: str) -> str | None:
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 24},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você cria títulos curtos para conversas. Responda SOMENTE com o título, "
                            "em português, com no máximo 6 palavras, sem aspas, sem ponto final "
                            "e sem a palavra 'Título'."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Pergunta do usuário:\n{pergunta[:500]}\n\nResposta do assistente:\n{resposta[:500]}",
                    },
                ],
            },
            timeout=30,
        )
        r.raise_for_status()
        bruto = r.json()["message"]["content"]
    except Exception:
        return None 
    
    linhas = bruto.strip().splitlines()
    if not linhas:
        return None
    titulo = re.sub(r"^t[ií]tulo\s*:\s*", "", linhas[0].strip(), flags=re.I)
    titulo = titulo.strip(" \"'“”*#.:")
    if not titulo or len(titulo) > 80: 
        return None
    return titulo