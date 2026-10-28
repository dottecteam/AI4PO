"""Desenha o grafo GraphRAG: painel global + um painel de zoom por comunidade.

No painel global, cor = comunidade e tamanho = grau (importancia no grafo).
So entram arestas com confianca >= GRAPH_CONF_MIN (mesmo criterio do retrieval).

Uso:
    python manage.py graphrag_draw --out /app/graphrag_graph.png
"""

import math

import matplotlib
matplotlib.use("Agg")  # sem display: renderiza direto no arquivo
import matplotlib.pyplot as plt
import networkx as nx

from django.core.management.base import BaseCommand

from ai.graphrag import CONF_MINIMA
from ai.models import Entidade, Relacao, Comunidade


class Command(BaseCommand):
    help = "Gera PNG do GraphRAG com painel global + zoom de cada comunidade."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="graphrag_graph.png")
        parser.add_argument("--projeto", type=int, default=0, help="Filtra por projeto (0 = todos).")

    def handle(self, *args, **opts):
        ents = Entidade.objects.all()
        if opts["projeto"]:
            ents = ents.filter(projeto_id=opts["projeto"])
        ents = list(ents)
        if not ents:
            self.stdout.write(self.style.WARNING("sem entidades no grafo."))
            return

        ids_ent = {e.id for e in ents}
        rels = [r for r in Relacao.objects.filter(confianca__gte=CONF_MINIMA)
                if r.origem_id in ids_ent and r.destino_id in ids_ent]

        # mapa entidade -> comunidade (para colorir); sem comunidade = cinza
        com_por_ent = {}
        coms = list(Comunidade.objects.all())
        for i, com in enumerate(coms):
            for eid in com.membros.values_list("id", flat=True):
                com_por_ent.setdefault(eid, i)

        G = nx.Graph()
        for e in ents:
            G.add_node(e.id, nome=e.nome)
        for r in rels:
            G.add_edge(r.origem_id, r.destino_id)

        base = plt.get_cmap("tab20")
        cinza = (0.78, 0.78, 0.78)
        nomes = {e.id: e.nome for e in ents}
        grau = dict(G.degree())

        n_com = len(coms)
        cols = 4
        linhas_com = math.ceil(max(n_com, 1) / cols)
        fig = plt.figure(figsize=(16, 8 + 4.2 * linhas_com))
        gs = fig.add_gridspec(1 + linhas_com, cols, height_ratios=[2.2] + [1] * linhas_com)

        # ---- painel global ----
        ax = fig.add_subplot(gs[0, :])
        pos = nx.spring_layout(G, k=1.4, iterations=60, seed=42)
        cores = [base(com_por_ent.get(n, -1) % 20) if n in com_por_ent else cinza for n in G.nodes()]
        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.25, edge_color="#999")
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=cores,
                               node_size=[40 + 55 * grau[n] for n in G.nodes()])
        # rotulo so dos mais conectados (senao vira ilegivel)
        top = sorted(G.nodes(), key=lambda n: grau[n], reverse=True)[:30]
        nx.draw_networkx_labels(G, pos, ax=ax, labels={n: nomes[n][:20] for n in top}, font_size=7)
        ax.set_title(f"Global — {G.number_of_nodes()} entidades, {G.number_of_edges()} arestas "
                     f"(conf >= {CONF_MINIMA}), cor = comunidade")
        ax.axis("off")

        # ---- um painel por comunidade (a divisao em si) ----
        for idx, com in enumerate(coms):
            ax = fig.add_subplot(gs[1 + idx // cols, idx % cols])
            membros = list(com.membros.filter(id__in=ids_ent))
            sub = G.subgraph([m.id for m in membros]).copy()
            if sub.number_of_nodes() == 0:
                ax.axis("off")
                continue
            pos_s = nx.spring_layout(sub, k=1.1, iterations=50, seed=7)
            nx.draw_networkx_edges(sub, pos_s, ax=ax, alpha=0.4, edge_color="#888")
            nx.draw_networkx_nodes(sub, pos_s, ax=ax, node_color=[base(idx % 20)] * sub.number_of_nodes(),
                                   node_size=[50 + 60 * dict(sub.degree())[n] for n in sub.nodes()])
            nx.draw_networkx_labels(sub, pos_s, ax=ax, labels={n: nomes[n][:18] for n in sub.nodes()}, font_size=6)
            resumo = (com.resumo or "").strip().replace("\n", " ")
            ax.set_title(f"C{com.id} · {com.tamanho} nos · projeto {com.projeto_id or '-'}\n"
                         + (resumo[:90] + "..." if len(resumo) > 90 else resumo), fontsize=7)
            ax.axis("off")

        # esconde subplots vazios da ultima linha
        for j in range(idx + 1, linhas_com * cols):
            fig.add_subplot(gs[1 + j // cols, j % cols]).axis("off")

        plt.tight_layout()
        plt.savefig(opts["out"], dpi=130)
        self.stdout.write(self.style.SUCCESS(f"imagem salva em {opts['out']}"))
