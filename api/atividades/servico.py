import logging

from django.db import transaction

from .models import Atividade

logger = logging.getLogger(__name__)


def registrar(usuario, acao, alvo=""):
    """Grava uma atividade. Nunca derruba a ação principal se o log falhar."""
    try:
        nome = (
            getattr(usuario, "nome", "")
            or getattr(usuario, "username", "")
            or str(usuario)
        )
        with transaction.atomic():  # savepoint: um erro aqui não anula a transação de fora
            Atividade.objects.create(
                usuario=usuario if getattr(usuario, "pk", None) else None,
                usuario_nome=nome[:150],
                acao=acao,
                alvo=(alvo or "")[:255],
            )
    except Exception:
        logger.exception("Falha ao registrar atividade '%s'", acao)