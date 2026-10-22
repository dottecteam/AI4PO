"""APIs do visualizador de grafo (GraphRAG) e do layout salvo pelo usuário.

- GrafoStatusView: progresso da ingestão do grafo de um documento (barra de %).
- GrafoDadosView: nós + arestas (+ posições salvas) de um projeto ou de todos (global).
- GrafoPosicoesView: grava as posições dos nós escolhidas pelo usuário (estilo Obsidian).

Tudo respeita o isolamento por usuário: só se vê grafo dos próprios projetos.
"""

from collections import defaultdict

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.models import Projeto, Documento

from .graphrag import CONF_MINIMA
from .models import Comunidade, Entidade, LayoutGrafo, ProgressoGrafo, Relacao


class GrafoStatusView(APIView):
    """Devolve o progresso da ingestão do grafo do documento (respeitando o dono)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, documento_id):
        documento = Documento.objects.filter(
            pk=documento_id, projeto__usuario_po=request.user
        ).first()
        if documento is None:
            return Response({"detail": "Documento não encontrado."}, status=404)

        prog = ProgressoGrafo.objects.filter(documento=documento).order_by("-iniciado_em").first()
        if prog is None:
            return Response({
                "status": "pendente", "total": 0, "processados": 0, "percentual": 0,
                "segundos_decorridos": None, "segundos_totais": None, "erro": "",
            })

        decorridos = None
        totais = None
        if prog.iniciado_em:
            referencia = prog.finalizado_em or timezone.now()
            decorridos = round((referencia - prog.iniciado_em).total_seconds(), 1)
            if prog.finalizado_em:
                totais = round((prog.finalizado_em - prog.iniciado_em).total_seconds(), 1)

        return Response({
            "status": prog.status,
            "total": prog.total_chunks,
            "processados": prog.chunks_processados,
            "percentual": prog.percentual,
            "segundos_decorridos": decorridos,
            "segundos_totais": totais,
            "erro": prog.erro,
        })


class GrafoDadosView(APIView):
    """Nós e arestas do grafo. `?projeto=<id>` filtra um projeto; sem ele, é o global."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        projeto_bruto = request.query_params.get("projeto")
        projeto_id = None
        if projeto_bruto not in (None, "", "null", "0"):
            try:
                projeto_id = int(projeto_bruto)
            except (TypeError, ValueError):
                return Response({"detail": "projeto inválido."}, status=400)
            # 404 silencioso: projeto de outro PO trata-se como inexistente.
            if not Projeto.objects.filter(pk=projeto_id, usuario_po=usuario).exists():
                return Response({"detail": "Projeto não encontrado."}, status=404)

        ents = list(
            Entidade.objects.filter(projeto__usuario_po=usuario)
            .filter(projeto_id=projeto_id) if projeto_id
            else Entidade.objects.filter(projeto__usuario_po=usuario)
        )
        ids_ent = {e.id for e in ents}
        rels_query = Relacao.objects.filter(confianca__gte=CONF_MINIMA)
        rels_query = rels_query.filter(projeto__usuario_po=usuario)
        if projeto_id:
            rels_query = rels_query.filter(projeto_id=projeto_id)
        rels = [r for r in rels_query if r.origem_id in ids_ent and r.destino_id in ids_ent]

        # cor por comunidade (índice), consistente com o painel de draw
        coms = list(Comunidade.objects.filter(projeto__usuario_po=usuario))
        if projeto_id:
            coms = [c for c in coms if c.projeto_id == projeto_id]
        com_por_ent = {}
        for i, com in enumerate(coms):
            for eid in com.membros.values_list("id", flat=True):
                com_por_ent.setdefault(eid, i)

        grau = defaultdict(int)
        for r in rels:
            grau[r.origem_id] += 1
            grau[r.destino_id] += 1

        layout = LayoutGrafo.objects.filter(usuario=usuario, projeto_id=projeto_id).first()
        pos = (layout.posicoes if layout else {}) or {}

        nos = [{
            "id": e.id, "nome": e.nome, "tipo": e.tipo, "descricao": e.descricao,
            "projeto": e.projeto_id, "comunidade": com_por_ent.get(e.id), "grau": grau.get(e.id, 0),
            "x": pos.get(str(e.id), {}).get("x"), "y": pos.get(str(e.id), {}).get("y"),
        } for e in ents]
        arestas = [{
            "origem": r.origem_id, "destino": r.destino_id, "tipo": r.tipo, "confianca": r.confianca,
        } for r in rels]

        return Response({"nos": nos, "arestas": arestas, "temLayout": bool(layout)})


class GrafoPosicoesView(APIView):
    """Grava as posições dos nós escolhidas pelo usuário (por projeto ou global)."""

    permission_classes = [IsAuthenticated]

    def put(self, request):
        usuario = request.user
        projeto_bruto = request.data.get("projeto")
        posicoes = request.data.get("posicoes") or {}
        if not isinstance(posicoes, dict):
            return Response({"detail": "posicoes deve ser um objeto {id: {x, y}}."}, status=400)

        projeto = None
        if projeto_bruto not in (None, "", "null", 0):
            try:
                projeto = Projeto.objects.get(pk=int(projeto_bruto), usuario_po=usuario)
            except (Projeto.DoesNotExist, TypeError, ValueError):
                return Response({"detail": "Projeto não encontrado."}, status=404)

        # sanitiza: só entradas {id: {x, y}} numéricas
        limpo = {}
        for chave, valor in posicoes.items():
            try:
                ent_id = int(chave)
                limpo[str(ent_id)] = {"x": float(valor["x"]), "y": float(valor["y"])}
            except (TypeError, ValueError, KeyError):
                continue

        layout, _ = LayoutGrafo.objects.get_or_create(usuario=usuario, projeto=projeto)
        layout.posicoes = limpo
        layout.save()
        return Response({"ok": True, "salvos": len(limpo)})
