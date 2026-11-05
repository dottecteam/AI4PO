from django.conf import settings
from django.db import models
from django.utils import timezone

ACOES = {
    "projeto_criado": "adicionou um novo projeto",
    "projeto_editado": "editou o projeto",
    "projeto_excluido": "excluiu o projeto",
    "documento_enviado": "enviou o documento",
    "documento_excluido": "excluiu o documento",
    "conversa_excluida": "excluiu a conversa",
}


class Atividade(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="atividades",
    )
    usuario_nome = models.CharField(max_length=150)
    acao = models.CharField(max_length=40, choices=[(k, k) for k in ACOES])
    alvo = models.CharField(max_length=255, blank=True)
    criado_em = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.usuario_nome} {ACOES.get(self.acao, self.acao)} {self.alvo}"