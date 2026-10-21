"""Comando de detecção de comunidades (task #13-2)."""

from django.core.management.base import BaseCommand

from ai import graphrag


class Command(BaseCommand):
    help = "Detecta comunidades no grafo (NetworkX) e grava na tabela Comunidade."

    def add_arguments(self, parser):
        parser.add_argument("--projeto", type=int, default=None, help="Restringe a um projeto.")
        parser.add_argument("--min-tamanho", type=int, default=4, help="Mínimo de nós por comunidade.")
        parser.add_argument("--sem-resumo", action="store_true", help="Pula o resumo via LLM (só partição).")

    def handle(self, *args, **opts):
        r = graphrag.detectar_comunidades(
            min_tamanho=opts["min_tamanho"], pular_resumo=opts["sem_resumo"], projeto_id=opts["projeto"]
        )
        self.stdout.write(self.style.SUCCESS(f"{r['comunidades']} comunidades em {r['segundos']}s"))