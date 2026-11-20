from pathlib import Path

from rest_framework import serializers

from .models import Projeto, Documento, Participacao
from .permissions import pode_gerenciar_projeto
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

# -------------------------
# Perfil do profissional (Task #15-2)
# -------------------------
class ProfissionalResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()
    email = serializers.EmailField()
    competencias = serializers.SerializerMethodField()
    total_projetos = serializers.SerializerMethodField()

    def get_competencias(self, funcionario):
        return [c.nome for c in funcionario.competencias.all()]

    def get_total_projetos(self, funcionario):
        return len({p.projeto_id for p in funcionario.participacoes.all()})


class ParticipacaoPerfilSerializer(serializers.ModelSerializer):
    projeto = serializers.SerializerMethodField()
    pode_editar = serializers.SerializerMethodField()

    class Meta:
        model = Participacao
        fields = ["id", "papel", "criado_em", "projeto", "pode_editar"]

    def get_pode_editar(self, participacao):
        request = self.context.get("request")
        return pode_gerenciar_projeto(getattr(request, "user", None), participacao.projeto)

    def get_projeto(self, participacao):
        projeto = participacao.projeto
        return {"id": projeto.id, "titulo": projeto.titulo, "status": projeto.status}


class PerfilProfissionalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()
    email = serializers.EmailField()
    competencias = serializers.SerializerMethodField()
    participacoes = serializers.SerializerMethodField()
    # Projetos em que o usuário logado pode registrar/alterar participações (Task #15-3)
    projetos_gerenciaveis = serializers.SerializerMethodField()

    def get_competencias(self, funcionario):
        return [
            {"id": c.id, "nome": c.nome}
            for c in sorted(funcionario.competencias.all(), key=lambda c: c.nome.lower())
        ]

    def get_participacoes(self, funcionario):
        # Trajetória do mais recente para o mais antigo
        participacoes = sorted(
            funcionario.participacoes.all(),
            key=lambda p: p.criado_em,
            reverse=True,
        )
        return ParticipacaoPerfilSerializer(
            participacoes, many=True, context=self.context
        ).data

    def get_projetos_gerenciaveis(self, funcionario):
        request = self.context.get("request")
        usuario = getattr(request, "user", None)
        if not (usuario and usuario.is_authenticated):
            return []
        projetos = Projeto.objects.order_by("titulo")
        if not usuario.is_staff:
            projetos = projetos.filter(usuario_po=usuario)
        return [{"id": p.id, "titulo": p.titulo} for p in projetos]
