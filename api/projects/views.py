from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.indexing import indexar_documento, FalhaDeEmbeddingError
from ai.extraction import (
    FormatoNaoSuportadoError,
    ArquivoNaoEncontradoError,
    FalhaDeDecodificacaoError,
)

from .models import Projeto
from .serializers import ProjetoSerializer, DocumentoUploadSerializer
from .upload_handlers import DocumentUploadSizeHandler
from .validators import MAX_UPLOAD_SIZE_BYTES, UPLOAD_SIZE_MESSAGE


MAX_MULTIPART_OVERHEAD_BYTES = 64 * 1024


def _upload_size_error_response():
    return Response(
        {"arquivo": [UPLOAD_SIZE_MESSAGE]},
        status=status.HTTP_400_BAD_REQUEST,
    )


def _declared_request_is_too_large(request):
    try:
        content_length = int(
            request.META.get("CONTENT_LENGTH", 0)
        )
    except (TypeError, ValueError):
        return False

    return content_length > (
        MAX_UPLOAD_SIZE_BYTES + MAX_MULTIPART_OVERHEAD_BYTES
    )


# -------------------------
# Projetos
# -------------------------

class ProjetoListCreateView(generics.ListCreateAPIView):
    queryset = Projeto.objects.all()
    serializer_class = ProjetoSerializer


class ProjetoDataView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Projeto.objects.all()
    serializer_class = ProjetoSerializer


# -------------------------
# Documentos
# -------------------------

class DocumentoUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, project_id):
        projeto = get_object_or_404(
            Projeto,
            pk=project_id
        )

        django_request = request._request

        if _declared_request_is_too_large(django_request):
            return _upload_size_error_response()

        django_request.upload_handlers.insert(
            0,
            DocumentUploadSizeHandler(django_request),
        )

        request_data = request.data

        if getattr(
            django_request,
            "document_upload_too_large",
            False
        ):
            return _upload_size_error_response()

        serializer = DocumentoUploadSerializer(
            data=request_data,
            context={
                "projeto": projeto,
                "request": request,
            },
        )

        serializer.is_valid(raise_exception=True)

        documento = serializer.save()

        documento.estado = "processando"
        documento.save(update_fields=["estado"])

        try:
            indexar_documento(documento)

            documento.estado = "processado"
            documento.save(update_fields=["estado"])

        except (
            FormatoNaoSuportadoError,
            ArquivoNaoEncontradoError,
            FalhaDeDecodificacaoError,
            FalhaDeEmbeddingError,
        ) as erro:

            documento.estado = "erro"
            documento.mensagem_erro = str(erro)

            documento.save(
                update_fields=[
                    "estado",
                    "mensagem_erro",
                ]
            )

        return Response(
            DocumentoUploadSerializer(
                documento,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )