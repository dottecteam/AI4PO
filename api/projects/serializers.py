from pathlib import Path

from rest_framework import serializers

from .models import Projeto, Documento, Participacao
from .validators import validate_document_upload


class ProjetoSerializer(serializers.ModelSerializer):

    # Busca o nome do PO
    po = serializers.CharField(
        source="usuario_po.nome",
        read_only=True
    )

    # ID do PO
    idPo = serializers.IntegerField(
        source="usuario_po_id",
        write_only=True
    )

    # Traduz o campo "criado_em"
    createdAt = serializers.DateTimeField(
        source="criado_em",
        read_only=True
    )

    class Meta:
        model = Projeto
        fields = [
            "id",
            "titulo",
            "descricao",
            "status",
            "po",
            "idPo",
            "createdAt",
        ]


class DocumentoUploadSerializer(serializers.ModelSerializer):

    arquivo = serializers.FileField(
        validators=[validate_document_upload]
    )

    class Meta:
        model = Documento
        fields = (
            "id",
            "projeto",
            "nome",
            "tipo",
            "arquivo",
            "data",
            "estado",
            "mensagem_erro",
        )
        read_only_fields = (
            "id",
            "projeto",
            "nome",
            "tipo",
            "data",
            "estado",
            "mensagem_erro",
        )

    def create(self, validated_data):
        arquivo = validated_data["arquivo"]
        filename = Path(arquivo.name).name

        return Documento.objects.create(
            projeto=self.context["projeto"],
            nome=filename,
            tipo=Path(filename).suffix.lower().lstrip("."),
            arquivo=arquivo,
        )

class ParticipacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participacao
        fields = ["id", "funcionario", "projeto", "papel", "criado_em"]
        read_only_fields = ["id", "criado_em"]
        validators = []

    def validate(self, data):
        funcionario = data.get("funcionario", getattr(self.instance, "funcionario", None))
        projeto = data.get("projeto", getattr(self.instance, "projeto", None))
        papel = data.get("papel", getattr(self.instance, "papel", None))

        existe = Participacao.objects.filter(
            funcionario=funcionario,
            projeto=projeto,
            papel__iexact=papel,
        )

        if self.instance:
            existe = existe.exclude(pk=self.instance.pk)

        if existe.exists():
            raise serializers.ValidationError(
                "Este profissional já está registrado neste projeto com este papel."
            )

        return data