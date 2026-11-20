from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import CookieJWTAuthentication
from .models import Competencia, Funcionario

NOME_MAX = 255
EMAIL_MAX = 254
ID_MAX_DIGITOS = 9


def _texto(valor):

    return valor.strip() if isinstance(valor, str) else ""


def serializar_competencia(competencia):
    return {"id": competencia.pk, "nome": competencia.nome}


def serializar_profissional(funcionario):
    competencias = sorted(funcionario.competencias.all(), key=lambda c: (c.nome.casefold(), c.pk))
    return {
        "id": funcionario.pk,
        "nome": funcionario.nome,
        "email": funcionario.email,
        "competencias": [serializar_competencia(c) for c in competencias],
    }


def _id_valido(valor):

    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor if 0 < valor < 10 ** ID_MAX_DIGITOS else None
    if isinstance(valor, str) and valor.strip().isdigit() and len(valor.strip()) <= ID_MAX_DIGITOS:
        return int(valor.strip()) or None
    return None


def validar_profissional(dados):

    nome = _texto(dados.get("nome"))
    email = _texto(dados.get("email")).lower()
    bruto = dados.get("competencias")
    erros, competencias = {}, []

    if not nome:
        erros["nome"] = ["O nome é obrigatório."]
    elif len(nome) > NOME_MAX:
        erros["nome"] = [f"O nome pode ter no máximo {NOME_MAX} caracteres."]

    if not email:
        erros["email"] = ["O e-mail é obrigatório."]
    elif len(email) > EMAIL_MAX:
        erros["email"] = [f"O e-mail pode ter no máximo {EMAIL_MAX} caracteres."]
    else:
        try:
            validate_email(email)
        except ValidationError:
            erros["email"] = ["Informe um e-mail válido."]
        else:
            if Funcionario.objects.filter(email__iexact=email).exists():
                erros["email"] = ["Já existe um profissional com este e-mail."]

    if not isinstance(bruto, list):
        erros["competencias"] = ["Envie a lista de competências do profissional."]
    elif not bruto:
        erros["competencias"] = ["Selecione ao menos uma competência."]
    else:
        ids = [_id_valido(v) for v in bruto]
        if any(i is None for i in ids):
            erros["competencias"] = ["A lista de competências tem valores inválidos."]
        else:
            ids = set(ids)
            competencias = list(Competencia.objects.filter(pk__in=ids))
            inexistentes = sorted(ids - {c.pk for c in competencias})
            if inexistentes:
                erros["competencias"] = [
                    f"Competências não encontradas: {', '.join(str(i) for i in inexistentes)}."
                ]

    return {"nome": nome, "email": email, "competencias": competencias}, erros


COMPETENCIA_MAX = 150


def validar_competencia(dados, ignorar_pk=None):
    """Nome obrigatório, até 150 caracteres e sem repetir outra competência (sem diferenciar maiúsculas)."""
    nome = " ".join(_texto(dados.get("nome")).split())
    erros = {}
    if not nome:
        erros["nome"] = ["O nome da competência é obrigatório."]
    elif len(nome) > COMPETENCIA_MAX:
        erros["nome"] = [f"O nome pode ter no máximo {COMPETENCIA_MAX} caracteres."]
    else:
        repetidas = Competencia.objects.filter(nome__iexact=nome)
        if ignorar_pk is not None:
            repetidas = repetidas.exclude(pk=ignorar_pk)
        if repetidas.exists():
            erros["nome"] = ["Já existe uma competência com este nome."]
    return nome, erros


def serializar_competencia_com_total(competencia):
    return {**serializar_competencia(competencia), "total_profissionais": competencia.total_profissionais}


class CompetenciaListView(APIView):
    """GET /api/competencias/ — catálogo de competências, para montar a busca e o cadastro.

    ?com_totais=1 inclui quantos profissionais têm cada competência (tela de gerenciamento).
    POST cadastra uma competência nova.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        competencias = Competencia.objects.order_by(Lower("nome"), "id")
        if request.query_params.get("com_totais") in ("1", "true"):
            competencias = competencias.annotate(total_profissionais=Count("funcionarios"))
            return Response([serializar_competencia_com_total(c) for c in competencias])
        return Response([serializar_competencia(c) for c in competencias])

    def post(self, request):
        dados = request.data if isinstance(request.data, dict) else {}
        nome, erros = validar_competencia(dados)
        if erros:
            return Response({"detail": "Corrija os campos destacados.", "campos": erros}, status=400)
        competencia = Competencia.objects.create(nome=nome)
        competencia.total_profissionais = 0
        return Response(serializar_competencia_com_total(competencia), status=201)


class CompetenciaDetailView(APIView):
    """PATCH renomeia (qualquer usuário logado); DELETE exclui (somente administrador).

    Excluir remove a competência de todos os profissionais que a possuem.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _alvo(self, pk):
        return get_object_or_404(
            Competencia.objects.annotate(total_profissionais=Count("funcionarios")), pk=pk
        )

    def patch(self, request, pk):
        competencia = self._alvo(pk)
        dados = request.data if isinstance(request.data, dict) else {}
        nome, erros = validar_competencia(dados, ignorar_pk=competencia.pk)
        if erros:
            return Response({"detail": "Corrija os campos destacados.", "campos": erros}, status=400)
        competencia.nome = nome
        competencia.save(update_fields=["nome"])
        return Response(serializar_competencia_com_total(competencia))

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {"detail": "Apenas administradores podem excluir competências."}, status=403
            )
        self._alvo(pk).delete()
        return Response(status=204)


class ProfissionalListCreateView(APIView):

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profissionais = Funcionario.objects.prefetch_related("competencias").order_by(Lower("nome"), "id")
        return Response([serializar_profissional(f) for f in profissionais])

    def post(self, request):
        dados = request.data if isinstance(request.data, dict) else {}
        limpos, erros = validar_profissional(dados)
        if erros:
            return Response({"detail": "Corrija os campos destacados.", "campos": erros}, status=400)

        try:
            with transaction.atomic():
                novo = Funcionario.objects.create(nome=limpos["nome"], email=limpos["email"])
                novo.competencias.set(limpos["competencias"])
        except IntegrityError:
            erros = {"email": ["Já existe um profissional com este e-mail."]}
            return Response({"detail": "Corrija os campos destacados.", "campos": erros}, status=400)

        return Response(serializar_profissional(novo), status=201)