from rest_framework import serializers
from backlog.models import Epico, Feature, PBI, Cenario


class EpicoSerializer(serializers.ModelSerializer):
    # Traduz os nomes dos campos para o front
    idProjeto = serializers.IntegerField(source='projeto_id')
    escopoMacro = serializers.ListField(child=serializers.CharField(), source='escopo_macro')
    resultadoEsperado = serializers.CharField(source='resultado')
    criteriosAceitacao = serializers.ListField(child=serializers.CharField(), source='criterios_de_aceitacao')
    createdAt = serializers.DateTimeField(source='criado_em', read_only=True)

    class Meta:
        model = Epico
        fields = ['id', 'titulo', 'descricao', 'objetivo', 'idProjeto', 'escopoMacro', 'resultadoEsperado', 'criteriosAceitacao', 'createdAt']


class FeatureSerializer(serializers.ModelSerializer):
    # Traduz os nomes dos campos para o front
    idEpico = serializers.IntegerField(source='epico_id')
    criteriosAceitacao = serializers.ListField(child=serializers.CharField(), source='criterios_de_aceitacao')
    createdAt = serializers.DateTimeField(source='criado_em', read_only=True)

    class Meta:
        model = Feature
        fields = ['id', 'idEpico', 'titulo', 'descricao', 'objetivo', 'criteriosAceitacao', 'createdAt']


class CenarioSerializer(serializers.ModelSerializer):
    # Não precisa de tradução
    class Meta:
        model = Cenario
        fields = ['id', 'dado', 'quando', 'entao']


class PBISerializer(serializers.ModelSerializer):
    # Traduz os nomes dos campos para o front
    idFeature = serializers.IntegerField(source='feature_id')

    # Monta UserStory a partir dos 3 campos no banco
    userStory = serializers.SerializerMethodField()

    cenarios = CenarioSerializer(many=True, read_only=True)

    createdAt = serializers.DateTimeField(source='criado_em', read_only=True)
    regras = serializers.CharField(source='regras_observacoes', required=False)

    class Meta:
        model = PBI
        fields = ['id', 'idFeature', 'titulo', 'userStory', 'regras', 'cenarios', 'createdAt']

    def get_userStory(self, obj):
        # Remonta o userStory a partir dos 3 campos no banco
        return {
            'como': obj.userstory_como,
            'quero': obj.userstory_quero,
            'paraQue': obj.userstory_paraque,
        }

    def create(self, validated_data):
        user_story = self.initial_data.get('userStory', {})
        cenarios_data = self.initial_data.get('cenarios', [])

        # Cria o PBI e separa o userStory nos 3 campos pro banco
        pbi = PBI.objects.create(
            feature_id=self.initial_data.get('idFeature'),
            titulo=validated_data['titulo'],
            userstory_como=user_story.get('como', ''),
            userstory_quero=user_story.get('quero', ''),
            userstory_paraque=user_story.get('paraQue', ''),
            regras_observacoes=validated_data.get('regras'),
        )

        # Cria cada cenário já vinculado a esse PBI (relação 1:N)
        for cenario in cenarios_data:
            Cenario.objects.create(
                pbi=pbi,
                dado=cenario.get('dado', ''),
                quando=cenario.get('quando', ''),
                entao=cenario.get('entao', ''),
            )

        return pbi

    def update(self, instance, validated_data):
        # Atualiza o que veio no payload e não muda o resto
        user_story = self.initial_data.get('userStory')
        cenarios_data = self.initial_data.get('cenarios')

        instance.titulo = validated_data.get('titulo', instance.titulo)
        instance.regras_observacoes = validated_data.get('regras', instance.regras_observacoes)

        if user_story is not None:
            instance.userstory_como = user_story.get('como', instance.userstory_como)
            instance.userstory_quero = user_story.get('quero', instance.userstory_quero)
            instance.userstory_paraque = user_story.get('paraQue', instance.userstory_paraque)

        instance.save()

        if cenarios_data is not None:
            instance.cenarios.all().delete()
            for cenario in cenarios_data:
                Cenario.objects.create(
                    pbi=instance,
                    dado=cenario.get('dado', ''),
                    quando=cenario.get('quando', ''),
                    entao=cenario.get('entao', ''),
                )

        return instance