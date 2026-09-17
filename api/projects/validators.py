from pathlib import Path

from django.core.exceptions import ValidationError


ALLOWED_EXTENSIONS = {".md", ".txt"}
ALLOWED_CONTENT_TYPES = {"text/markdown", "text/plain"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
UPLOAD_REQUIREMENTS_MESSAGE = (
    "Formato não suportado. Envie um arquivo .md ou .txt de até 10 MB."
)
UPLOAD_SIZE_MESSAGE = "Tamanho máximo excedido. Envie um arquivo de até 10 MB."


def validate_document_upload(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()

    if (
        extension not in ALLOWED_EXTENSIONS
        or uploaded_file.content_type not in ALLOWED_CONTENT_TYPES
    ):
        raise ValidationError(UPLOAD_REQUIREMENTS_MESSAGE)

    if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(UPLOAD_SIZE_MESSAGE)
