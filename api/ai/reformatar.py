import json
import logging

import requests
from decouple import config

from .models import MensagemChat
from .prompts import montar_system_prompt

logger = logging.getLogger(__name__)

OLLAMA_URL = config("OLLAMA_URL", default="http://host.docker.internal:11434")
MODEL = config("OLLAMA_MODEL", default="llama3.2:3b")

# Mantém o modelo carregado na memória entre as mensagens. Sem isso o Ollama
# descarrega o modelo depois de 5 min parado, e a próxima chamada paga o
# tempo de carregar (isso explica "às vezes funciona, às vezes dá timeout").
KEEP_ALIVE = config("OLLAMA_KEEP_ALIVE", default="30m")
# Limite de tokens da resposta da reformatação. Evita geração sem fim e
# deixa o tempo máximo previsível. Se uma resposta ficar cortada, aumente.
NUM_PREDICT = config("OLLAMA_REFORMAT_NUM_PREDICT", default=1200, cast=int)
REFORMAT_TIMEOUT = config("OLLAMA_REFORMAT_TIMEOUT", default=300, cast=int)
ROUTER_TIMEOUT = config("OLLAMA_ROUTER_TIMEOUT", default=60, cast=int)

TIPOS_VALIDOS = {"pbi", "feature", "epico"}
INTENCOES_VALIDAS = {"reformatar", "ajustar", "conversar"}

REGRA_SAIDA = (
    "Responda SOMENTE com a estrutura pedida no system prompt, sem introdução, "
    "sem comentários antes ou depois, sem repetir o rascunho original e sem "
    "reutilizar os nomes/títulos de exemplo citados nas regras — eles são só "
    "formato, o conteúdo tem que vir do rascunho abaixo.\n\n"
)

# ==========================================
# ROTEADOR: decide o que fazer com a mensagem
# ==========================================
PROMPT_ROTEADOR = """Você classifica a intenção da mensagem de um Product Owner (PO) em um chat de gestão de backlog.
Responda apenas com o JSON pedido.

Intenções:
- "reformatar": o PO traz um rascunho de requisito (PBI, Feature ou Épico) para ser reescrito e padronizado, ou descreve uma necessidade de produto para virar um requisito estruturado.
- "ajustar": SÓ vale se a última resposta do assistente foi uma reformatação. O PO pede uma mudança nessa versão (encurtar, dividir, adicionar, remover ou trocar algo).
- "conversar": pergunta, dúvida, pedido de explicação ou busca de informação sobre projetos, regras ou decisões.

Tipo do requisito: "pbi", "feature" ou "epico", conforme o PO mencionar. Se não mencionar, use "pbi".

Exemplos:
- (última resposta foi reformatação: não) "Reformate: o usuário precisa exportar o relatório em PDF" -> reformatar, pbi
- (última resposta foi reformatação: não) "Quero um épico de integração com sistemas de pagamento, com Pix e cartão" -> reformatar, epico
- (última resposta foi reformatação: não) "Épico de pagamentos: feature de Pix com os PBIs gerar QR code e confirmar pagamento, e feature de cartão com o PBI cobrar parcelado" -> reformatar, epico
- (última resposta foi reformatação: não) "Feature de filtros no backlog: PBI de filtrar por status e PBI de salvar o filtro escolhido" -> reformatar, feature
- (última resposta foi reformatação: não) "Como funciona o fluxo de aprovação do projeto?" -> conversar, pbi
- (última resposta foi reformatação: não) "Encurte isso" -> conversar, pbi
- (última resposta foi reformatação: sim) "Deixe os critérios de aceite mais curtos" -> ajustar, pbi
- (última resposta foi reformatação: sim) "Esse PBI está grande demais, divida em dois" -> ajustar, pbi
- (última resposta foi reformatação: sim) "Qual a diferença entre feature e épico?" -> conversar, pbi
"""

SCHEMA_INTENCAO = {
    "type": "object",
    "properties": {
        "intencao": {"type": "string", "enum": sorted(INTENCOES_VALIDAS)},
        "tipo": {"type": "string", "enum": sorted(TIPOS_VALIDOS)},
    },
    "required": ["intencao", "tipo"],
}


class ReformatacaoError(Exception):
    """Falha ao reformatar. `mensagem` é segura para mostrar ao usuário."""

    def __init__(self, mensagem, status=502):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def classificar_intencao(message, ultima_foi_reformatacao):
    """Devolve (intencao, tipo). Em qualquer falha, segue como conversa normal."""
    contexto = "sim" if ultima_foi_reformatacao else "não"
    try:
        resposta = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": PROMPT_ROTEADOR},
                    {
                        "role": "user",
                        "content": (
                            f"(última resposta foi reformatação: {contexto})\n"
                            f"Mensagem do PO:\n{message[:1500]}"
                        ),
                    },
                ],
                "format": SCHEMA_INTENCAO,
                "stream": False,
                "keep_alive": KEEP_ALIVE,
                # a resposta é um JSON minúsculo; o limite impede que o
                # roteador gaste tempo à toa
                "options": {"temperature": 0, "num_predict": 80},
            },
            timeout=ROUTER_TIMEOUT,
        )
        resposta.raise_for_status()
        dados = json.loads(resposta.json()["message"]["content"])
        intencao = dados.get("intencao")
        tipo = dados.get("tipo")
    except (requests.exceptions.RequestException, KeyError, ValueError):
        logger.exception("Falha ao classificar a intenção; seguindo como conversa")
        return "conversar", "pbi"

    if intencao not in INTENCOES_VALIDAS:
        intencao = "conversar"
    if tipo not in TIPOS_VALIDOS:
        tipo = "pbi"
    return intencao, tipo


# ==========================================
# REFORMATAÇÃO
# ==========================================
def instrucao_rascunho(requisito):
    return f"{REGRA_SAIDA}--- RASCUNHO ---\n{requisito}\n--- FIM DO RASCUNHO ---"


def instrucao_ajuste(pedido):
    return (
        "Aplique o ajuste abaixo à sua última versão e responda SOMENTE com a "
        "estrutura completa atualizada, sem introdução e sem comentários.\n\n"
        f"--- AJUSTE ---\n{pedido}\n--- FIM DO AJUSTE ---"
    )


def reformatacao_pendente(conversa):
    """A última resposta da IA na conversa, se ela foi uma reformatação."""
    ultima = (
        conversa.mensagens.filter(papel="assistant").order_by("-id").first()
    )
    if ultima and (ultima.metadata or {}).get("tipo") == "reformatado":
        return ultima
    return None


def gerar_reformatacao(mensagem, tipo, anterior=None):
    """Reformata um rascunho novo ou aplica um ajuste à versão `anterior`."""
    if anterior is not None:
        tipo = anterior.metadata["requisito_tipo"]
        original = anterior.metadata["original"]
        messages = [
            {"role": "system", "content": montar_system_prompt(tipo)},
            {"role": "user", "content": instrucao_rascunho(original)},
            {"role": "assistant", "content": anterior.conteudo},
            {"role": "user", "content": instrucao_ajuste(mensagem)},
        ]
    else:
        original = mensagem
        messages = [
            {"role": "system", "content": montar_system_prompt(tipo)},
            {"role": "user", "content": instrucao_rascunho(original)},
        ]

    try:
        resposta = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": messages,
                "stream": False,
                "keep_alive": KEEP_ALIVE,
                "options": {"temperature": 0.1, "num_predict": NUM_PREDICT},
            },
            timeout=REFORMAT_TIMEOUT,
        )
        resposta.raise_for_status()
    except requests.exceptions.Timeout:
        logger.exception("Timeout ao chamar o Ollama (%ss)", REFORMAT_TIMEOUT)
        raise ReformatacaoError(
            "A IA demorou demais para responder. Tente novamente ou envie um "
            "rascunho menor."
        )
    except requests.exceptions.RequestException:
        logger.exception("Falha ao chamar o Ollama")
        raise ReformatacaoError("Falha ao comunicar com o serviço de IA.")

    dados = resposta.json()
    reformatado = dados.get("message", {}).get("content", "").strip()

    if not reformatado:
        raise ReformatacaoError("O modelo não retornou nenhum conteúdo.")
    if reformatado.startswith('{"'):
        raise ReformatacaoError(
            "O modelo retornou um formato inesperado. Tente novamente."
        )
    # done_reason == "length" quer dizer que bateu no limite de tokens e a
    # resposta veio cortada no meio; melhor avisar do que entregar pela metade
    if dados.get("done_reason") == "length":
        logger.warning("Reformatação cortada pelo limite de %s tokens", NUM_PREDICT)
        raise ReformatacaoError(
            "A resposta ficou longa demais e foi cortada. Envie o rascunho em "
            "partes menores."
        )

    return {"tipo": tipo, "original": original, "reformatado": reformatado}


def salvar_reformatacao(conversa, mensagem, resultado):
    """Grava o par pergunta/resposta com o metadata que guarda o original."""
    MensagemChat.objects.bulk_create(
        [
            MensagemChat(conversa=conversa, papel="user", conteudo=mensagem),
            MensagemChat(
                conversa=conversa,
                papel="assistant",
                conteudo=resultado["reformatado"],
                metadata={
                    "tipo": "reformatado",
                    "requisito_tipo": resultado["tipo"],
                    "original": resultado["original"],
                },
            ),
        ]
    )
    conversa.save()  # atualiza atualizado_em pra conversa subir na sidebar