from pathlib import Path

from rest_framework import serializers

from .models import Documento
from .validators import validate_document_upload


class DocumentoUploadSerializer(serializers.ModelSerializer):
    arquivo = serializers.FileField(validators=[validate_document_upload])

    class Meta:
        model = Documento
        fields = ("id", "projeto", "nome", "tipo", "arquivo", "data", "estado", "mensagem_erro")
        read_only_fields = ("id", "projeto", "nome", "tipo", "data", "estado", "mensagem_erro")

    def create(self, validated_data):
        arquivo = validated_data["arquivo"]
        filename = Path(arquivo.name).name

        return Documento.objects.create(
            projeto=self.context["projeto"],
            nome=filename,
            tipo=Path(filename).suffix.lower().lstrip("."),
            arquivo=arquivo,
        )
