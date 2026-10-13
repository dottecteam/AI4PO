from rest_framework import serializers
from .models import Conversa, MensagemChat


class ConversaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversa
        fields = ("id", "titulo", "projeto", "atualizado_em")


class MensagemChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = MensagemChat
        fields = ("id", "papel", "conteudo", "anexo_nome", "criado_em")


class ConversaDetalheSerializer(serializers.ModelSerializer):
    mensagens = MensagemChatSerializer(many=True, read_only=True)

    class Meta:
        model = Conversa
        fields = ("id", "titulo", "projeto", "criado_em", "atualizado_em", "mensagens")