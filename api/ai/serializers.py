from rest_framework import serializers
from .models import Conversa, MensagemChat
from .validacao_chat import resumo_curto


class ConversaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversa
        fields = ("id", "titulo", "projeto", "atualizado_em")


class MensagemChatSerializer(serializers.ModelSerializer):
    conteudo = serializers.SerializerMethodField()
    fontes = serializers.SerializerMethodField()
    validacao = serializers.SerializerMethodField()
    pergunta = serializers.SerializerMethodField()
    acao = serializers.SerializerMethodField()

    class Meta:
        model = MensagemChat
        fields = ("id", "papel", "conteudo", "anexo_nome", "criado_em", "fontes", "validacao", "pergunta", "acao")

    def get_pergunta(self, obj):
        return (obj.metadata or {}).get("pergunta")

    def get_acao(self, obj):
        acao = (obj.metadata or {}).get("acao")
        return {**acao, "mensagem_id": obj.id} if acao else None

    def get_validacao(self, obj):
        return (obj.metadata or {}).get("validacao")

    def get_fontes(self, obj):
        return (obj.metadata or {}).get("fontes", [])

    def get_conteudo(self, obj):
        validacao = self.get_validacao(obj)
        # com validação, o histórico mostra o texto curto (igual ao da hora do envio)
        # e o cartão vem do campo `validacao`
        return resumo_curto(validacao) if validacao else obj.conteudo


class ConversaDetalheSerializer(serializers.ModelSerializer):
    mensagens = MensagemChatSerializer(many=True, read_only=True)

    class Meta:
        model = Conversa
        fields = ("id", "titulo", "projeto", "criado_em", "atualizado_em", "mensagens")