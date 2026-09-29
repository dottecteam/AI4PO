from django.db import migrations
# Importo a classe VectorExtension do pacote pgvector, que sabe exatamente
# como registrar extensões nativas no PostgreSQL pelo mecanismo de migrations do Django
from pgvector.django import VectorExtension

class Migration(migrations.Migration):

    # Lista de dependências vazia porque esta deve ser a primeiríssima migração a rodar no app 'ai',
    # antes mesmo de qualquer tabela com colunas de vetor tentar ser criada
    dependencies = [
    ]

    operations = [
        # Esta operação executa internamente o comando SQL "CREATE EXTENSION IF NOT EXISTS vector;"
        # no PostgreSQL. Sem ativar essa extensão antes, o banco rejeita qualquer campo do tipo VectorField
        VectorExtension(),
    ]

    