# Ajusta a dimensão do embedding de 1536 para 768, que é o tamanho gerado pelo
# nomic-embed-text (modelo padrão de OLLAMA_EMBEDDING_MODEL). Com 1536 o Postgres
# rejeitava toda gravação real com "expected 1536 dimensions, not 768".
#
# O índice HNSW é removido antes e recriado depois: alterar o tipo da coluna com o
# índice no lugar obriga o Postgres a reconstruí-lo, o que falha se já existir linha
# gravada com a dimensão antiga.
#
# Atenção: chunks indexados antes desta migração precisam ser reindexados, porque não
# existe conversão de vetor 1536 para 768.

import pgvector.django.indexes
import pgvector.django.vector
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0003_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='chunkdoc',
            name='chunk_vector_cosine_idx',
        ),
        migrations.AlterField(
            model_name='chunkdoc',
            name='embedding',
            field=pgvector.django.vector.VectorField(dimensions=768),
        ),
        migrations.AddIndex(
            model_name='chunkdoc',
            index=pgvector.django.indexes.HnswIndex(ef_construction=64, fields=['embedding'], m=16, name='chunk_vector_cosine_idx', opclasses=['vector_cosine_ops']),
        ),
    ]
