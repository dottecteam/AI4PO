from django.db.models import Count, Q
from django.db.models.functions import Lower
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import CookieJWTAuthentication
from .models import Competencia, Funcionario

ID_MAX_DIGITOS = 9
MAX_COMPETENCIAS = 30

CRITERIOS = {
    "afinidade": (
        "Percentual das competências buscadas que o profissional possui "
        "(competências correspondentes ÷ competências buscadas × 100)."
    ),
    "ordenacao": [
        "1º maior afinidade (mais competências buscadas)",
        "2º maior foco: menos competências fora da busca "
        "(correspondentes ÷ total de competências do profissional)",
        "3º nome em ordem alfabética",
    ],
}


def _separar(valores):
    itens = []
    for valor in valores:
        itens.extend(parte.strip() for parte in valor.split(","))
    return [i for i in itens if i]


def _erro(campo, mensagens):
    return Response({"detail": "Corrija os parâmetros da busca.", "campos": {campo: mensagens}}, status=400)


def _percentual(parte, todo):
    return round(100 * parte / todo, 1)


def _resumo(competencia):
    return {"id": competencia.pk, "nome": competencia.nome}


class BuscaProfissionaisView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ids_brutos = _separar(request.query_params.getlist("competencias"))
        nomes = _separar(request.query_params.getlist("nomes"))

        if not ids_brutos and not nomes:
            return _erro("competencias", [
                "Informe ao menos uma competência (competencias=1,2 ou nomes=Python,Django)."
            ])
        if len(ids_brutos) + len(nomes) > MAX_COMPETENCIAS:
            return _erro("competencias", [f"Informe no máximo {MAX_COMPETENCIAS} competências por busca."])

        ids_invalidos = [i for i in ids_brutos if not (i.isdigit() and len(i) <= ID_MAX_DIGITOS)]
        if ids_invalidos:
            return _erro("competencias", [f"Ids inválidos: {', '.join(ids_invalidos)}."])

        buscadas = {}
        ids = {int(i) for i in ids_brutos}
        if ids:
            buscadas.update({c.pk: c for c in Competencia.objects.filter(pk__in=ids)})
            inexistentes = sorted(ids - set(buscadas))
            if inexistentes:
                return _erro("competencias", [
                    f"Competências não encontradas: {', '.join(str(i) for i in inexistentes)}."
                ])

        nomes_inexistentes = []
        nomes_unicos = {}
        for n in nomes:
            nomes_unicos.setdefault(n.casefold(), n)
        for nome in nomes_unicos.values():
            achadas = list(Competencia.objects.filter(nome__iexact=nome))
            if not achadas:
                nomes_inexistentes.append(nome)
            buscadas.update({c.pk: c for c in achadas})
        if nomes_inexistentes:
            return _erro("nomes", [f"Competências não encontradas: {', '.join(nomes_inexistentes)}."])

        buscadas_ordenadas = sorted(buscadas.values(), key=lambda c: (c.nome.casefold(), c.pk))
        ids_buscados = [c.pk for c in buscadas_ordenadas]

        profissionais = (
            Funcionario.objects
            .annotate(
                correspondencias=Count("competencias", filter=Q(competencias__in=ids_buscados)),
                total_competencias=Count("competencias"),
            )
            .filter(correspondencias__gt=0)
            .order_by("-correspondencias", "total_competencias", Lower("nome"), "id")
            .prefetch_related("competencias")
        )

        resultados = []
        for p in profissionais:
            dele = sorted(p.competencias.all(), key=lambda c: (c.nome.casefold(), c.pk))
            ids_dele = {c.pk for c in dele}
            resultados.append({
                "id": p.pk,
                "nome": p.nome,
                "email": p.email,
                "afinidade": _percentual(p.correspondencias, len(buscadas_ordenadas)),
                "competencias_correspondentes": [_resumo(c) for c in dele if c.pk in buscadas],
                "competencias_faltantes": [_resumo(c) for c in buscadas_ordenadas if c.pk not in ids_dele],
                "total_competencias": p.total_competencias,
                "foco": _percentual(p.correspondencias, p.total_competencias),
            })

        return Response({
            "criterios": {
                "competencias_buscadas": [_resumo(c) for c in buscadas_ordenadas],
                **CRITERIOS,
            },
            "total": len(resultados),
            "resultados": resultados,
        })