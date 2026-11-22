from datetime import datetime

from django.db.models import Count, Q
from django.db.models.functions import Lower, TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.models import Documento, Projeto
from users.authentication import CookieJWTAuthentication
from users.models import Competencia, Funcionario
from users.permissions import escopo

from .models import Conversa, MensagemChat


class ResumoDashboardView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projetos = Projeto.objects.all()
        documentos = Documento.objects.all()
        conversas = Conversa.objects.all()
        validacoes = MensagemChat.objects.filter(
            papel="assistant", metadata__has_key="validacao"
        )

        if not getattr(request.user, "is_admin", False):
            projetos = projetos.filter(usuario_po=request.user)
            documentos = documentos.filter(projeto__usuario_po=request.user)
            conversas = conversas.filter(usuario_po=request.user)
            validacoes = validacoes.filter(conversa__usuario_po=request.user)

        docs = documentos.aggregate(
            total=Count("id"),
            processados=Count("id", filter=Q(estado="processado")),
            processando=Count("id", filter=Q(estado="processando")),
            com_erro=Count("id", filter=Q(estado="erro")),
        )
        docs["percentual_indexado"] = (
            round(docs["processados"] * 100 / docs["total"]) if docs["total"] else 0
        )

        return Response({
            "projetos": projetos.count(),
            "documentos": docs,
            "conversas": conversas.count(),
            "validacoes": validacoes.count(),
        })

MESES_GRAFICO = 6
TOP_COMPETENCIAS = 6
TOP_PROFISSIONAIS = 5


def _ultimos_meses(hoje, quantidade):
    """[(ano, mes), ...] do mais antigo ao mês atual."""
    ano, mes = hoje.year, hoje.month
    meses = []
    for _ in range(quantidade):
        meses.append((ano, mes))
        mes -= 1
        if mes == 0:
            ano, mes = ano - 1, 12
    return list(reversed(meses))


class GraficosDashboardView(APIView):
    """GET /api/dashboard/graficos/ — séries para os gráficos do dashboard.

    Projetos seguem a mesma regra de visibilidade das telas de projeto
    (users.permissions.escopo); profissionais e competências são globais,
    como na tela de profissionais.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projetos = Projeto.objects.filter(**escopo(request.user, "usuario_po"))

        meses = _ultimos_meses(timezone.localdate(), MESES_GRAFICO)
        inicio = timezone.make_aware(datetime(meses[0][0], meses[0][1], 1))
        por_mes = {
            (linha["mes"].year, linha["mes"].month): linha["total"]
            for linha in projetos.filter(criado_em__gte=inicio)
            .annotate(mes=TruncMonth("criado_em"))
            .values("mes")
            .annotate(total=Count("id"))
        }

        por_status = dict(projetos.values_list("status").annotate(total=Count("id")))

        # Projetos distintos por profissional (um profissional com 2 papéis no
        # mesmo projeto conta 1 projeto)
        profissionais = Funcionario.objects.annotate(
            total_projetos=Count("participacoes__projeto", distinct=True)
        )
        totais = [p.total_projetos for p in profissionais]
        total_profissionais = len(totais)

        top_profissionais = sorted(
            (p for p in profissionais if p.total_projetos > 0),
            key=lambda p: (-p.total_projetos, p.nome.casefold()),
        )[:TOP_PROFISSIONAIS]

        top_competencias = (
            Competencia.objects.annotate(total=Count("funcionarios"))
            .filter(total__gt=0)
            .order_by("-total", Lower("nome"))[:TOP_COMPETENCIAS]
        )

        return Response({
            "projetos_por_mes": [
                {"mes": f"{ano:04d}-{mes:02d}", "total": por_mes.get((ano, mes), 0)}
                for ano, mes in meses
            ],
            "projetos_por_status": [
                {"status": valor, "total": por_status.get(valor, 0)}
                for valor, _ in Projeto.Status.choices
            ],
            "equipe": {
                "profissionais": total_profissionais,
                "media_projetos_por_profissional": (
                    round(sum(totais) / total_profissionais, 1) if total_profissionais else 0
                ),
                "sem_projeto": sum(1 for t in totais if t == 0),
                "competencias": Competencia.objects.count(),
            },
            "top_competencias": [
                {"id": c.id, "nome": c.nome, "total": c.total} for c in top_competencias
            ],
            "top_profissionais": [
                {"id": p.id, "nome": p.nome, "total": p.total_projetos} for p in top_profissionais
            ],
        })
