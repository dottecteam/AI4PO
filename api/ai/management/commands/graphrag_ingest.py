"""Comando de ingestão do grafo (task #13-1).

Exemplos:
    python manage.py graphrag_ingest --limite 20
    python manage.py graphrag_ingest --projeto 1 --lote 3
    python manage.py graphrag_ingest --documento 4
    python manage.py graphrag_ingest --completo   # reprocessa tudo (pós-mudança no filtro)
"""

from django.core.management.base import BaseCommand, CommandError

from ai import graphrag


class Command(BaseCommand):
    help = "Extrai entidades e relações dos chunks indexados e grava no grafo."

    def add_arguments(self, parser):
        parser.add_argument("--limite", type=int, default=0, help="Máx. de chunks na ingestão (0 = todos).")
        parser.add_argument("--projeto", type=int, default=None, help="Restringe a ingestão a um projeto.")
        parser.add_argument("--documento", type=int, default=None, help="Restringe a ingestão a um documento.")
        parser.add_argument("--lote", type=int, default=3, help="Chunks por chamada ao LLM.")
        parser.add_argument("--completo", action="store_true", help="Reprocessa todos os chunks (ignora o marcador incremental).")

    def handle(self, *args, **opts):
        try:
            r = graphrag.ingestir(
                limite=opts["limite"] or None,
                projeto_id=opts["projeto"],
                documento_id=opts["documento"],
                lote=opts["lote"],
                reprocessar=opts["completo"],
            )
        except graphrag.ErroDeGrafo as erro:
            raise CommandError(str(erro))
        self.stdout.write(self.style.SUCCESS(f"Ingestão concluída: {r}"))
