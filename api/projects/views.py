from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Projeto
from .serializers import DocumentoUploadSerializer
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
        content_length = int(request.META.get("CONTENT_LENGTH", 0))
    except (TypeError, ValueError):
        return False

    return content_length > MAX_UPLOAD_SIZE_BYTES + MAX_MULTIPART_OVERHEAD_BYTES


class DocumentoUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, project_id):
        projeto = get_object_or_404(Projeto, pk=project_id)
        django_request = request._request

        if _declared_request_is_too_large(django_request):
            return _upload_size_error_response()

        django_request.upload_handlers.insert(
            0,
            DocumentUploadSizeHandler(django_request),
        )
        request_data = request.data
        if getattr(django_request, "document_upload_too_large", False):
            return _upload_size_error_response()

        serializer = DocumentoUploadSerializer(
            data=request_data,
            context={"projeto": projeto, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        documento = serializer.save()

        return Response(
            DocumentoUploadSerializer(
                documento,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )
