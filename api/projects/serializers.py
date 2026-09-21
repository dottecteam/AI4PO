from rest_framework import serializers
from projects.models import Projeto

class ProjetoSerializer(serializers.ModelSerializer):
    # Busca o nome do PO
    po = serializers.CharField(source='usuario_po.get_full_name', read_only=True)
    idPo = serializers.IntegerField(source='usuario_po_id', write_only=True)

    # Traduz o campo "criado_em"
    createdAt = serializers.DateTimeField(source='criado_em', read_only = True)

    class Meta:
        model = Projeto
        fields = ['id', 'titulo', 'descricao', 'status', 'po', 'idPo', 'createdAt']