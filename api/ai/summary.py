"""Resumo rolante da conversa (memória de longo prazo).

A janela deslizante (history.py) só enxerga as mensagens recentes. Quando ela
enche, as mensagens mais antigas são condensadas num resumo salvo em
`Conversa.resumo`, que entra no prompt de sistema nos turnos seguintes.

`Conversa.resumido_ate_id` guarda o id da última mensagem já incorporada ao
resumo: o histórico carregado depois dele nunca repete o que o resumo cobre.
"""

import logging

import requests
from decouple import config
from django.db import connection

from .models import Conversa

logger = logging.getLogger(__name__)

OLLAMA_URL = config("OLLAMA_URL", default="http://host.docker.internal:11434")
MODEL = config("OLLAMA_MODEL", default="llama3.2:3b")
NUM_CTX = config("OLLAMA_NUM_CTX", default=8192, cast=int)
TIMEOUT = 120

# Quando as mensagens ainda não resumidas passam deste número, as mais antigas
# são condensadas, mantendo MANTER_RECENTES mensagens "cruas" na janela.
MAX_NAO_RESUMIDAS = 8
MANTER_RECENTES = 4
MAX_CHARS_POR_MSG = 1500  # mensagens enormes (ex.: respostas longas) são truncadas no resumo

PROMPT_RESUMO = (
    "Você mantém o resumo de uma conversa entre um Product Owner e um assistente de IA. "
    "Atualize o resumo atual incorporando as novas mensagens. Preserve: nomes de projetos, "
    "decisões tomadas, dados e números importantes, pendências e o assunto em andamento. "
    "Descarte cumprimentos e detalhes irrelevantes. Escreva em português, em texto corrido, "
    "com no máximo 150 palavras. Responda SOMENTE com o resumo atualizado."
)

PROMPT_TITULO = (
    "Crie um título curto (máximo 6 palavras) para a conversa resumida abaixo. "
    "Responda SOMENTE com o título, sem aspas e sem ponto final."
)


def _chamar(system, user):
    resposta = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"num_ctx": NUM_CTX, "temperature": 0.2},
        },
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    return (resposta.json().get("message", {}).get("content") or "").strip()


def _transcricao(mensagens):
    linhas = []
    for m in mensagens:
        quem = "PO" if m.papel == "user" else "Assistente"
        texto = m.conteudo[:MAX_CHARS_POR_MSG]
        if m.anexo_nome:
            texto += f" [anexo: {m.anexo_nome}]"
        linhas.append(f"{quem}: {texto}")
    return "\n".join(linhas)


def atualizar_resumo(conversa_id):
    """Condensa as mensagens antigas no resumo, se a janela já encheu.

    Pensada para rodar fora do ciclo da requisição (thread). Falhar aqui é
    inofensivo: as mensagens continuam no banco e a próxima tentativa refaz.
    """
    try:
        conversa = Conversa.objects.get(pk=conversa_id)
        pendentes = list(
            conversa.mensagens.filter(id__gt=conversa.resumido_ate_id).order_by("id")
        )
        if len(pendentes) <= MAX_NAO_RESUMIDAS:
            return

        a_resumir = pendentes[:-MANTER_RECENTES]
        novo_resumo = _chamar(
            PROMPT_RESUMO,
            f"Resumo atual:\n{conversa.resumo or '(vazio)'}\n\n"
            f"Novas mensagens:\n{_transcricao(a_resumir)}\n\nResumo atualizado:",
        )
        if not novo_resumo:
            logger.warning("Resumo vazio para a conversa %s; mantendo o anterior.", conversa_id)
            return

        campos = {"resumo": novo_resumo, "resumido_ate_id": a_resumir[-1].id}

        # Título "de verdade" na primeira vez que a conversa ganha resumo
        if not conversa.resumo:
            titulo = _chamar(PROMPT_TITULO, novo_resumo).strip('"\' .\n')[:120]
            if titulo:
                campos["titulo"] = titulo

        # Só grava se ninguém avançou o resumo nesse meio-tempo (duas threads simultâneas).
        # update() não toca em atualizado_em, então a conversa não muda de posição na sidebar.
        gravou = Conversa.objects.filter(
            pk=conversa.pk, resumido_ate_id=conversa.resumido_ate_id
        ).update(**campos)
        logger.info(
            "Resumo da conversa %s %s (cobre até a mensagem %s).",
            conversa_id, "atualizado" if gravou else "descartado (corrida)", a_resumir[-1].id,
        )
    except Exception:
        logger.exception("Falha ao atualizar o resumo da conversa %s", conversa_id)
    finally:
        connection.close()  # conexões de thread não são fechadas automaticamente