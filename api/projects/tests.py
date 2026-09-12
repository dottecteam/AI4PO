from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from .validators import validate_document_upload


class DocumentUploadValidatorTests(SimpleTestCase):
    def test_accepts_supported_text_files(self):
        supported_files = (
            ("requirements.txt", "text/plain"),
            ("requirements.md", "text/markdown"),
            ("REQUIREMENTS.MD", "text/plain"),
        )

        for filename, content_type in supported_files:
            with self.subTest(filename=filename, content_type=content_type):
                uploaded_file = SimpleUploadedFile(
                    filename,
                    b"document content",
                    content_type=content_type,
                )

                validate_document_upload(uploaded_file)

    def test_rejects_unsupported_extension_and_explains_limits(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.pdf",
            b"document content",
            content_type="application/pdf",
        )

        with self.assertRaises(ValidationError) as error:
            validate_document_upload(uploaded_file)

        message = str(error.exception)
        self.assertIn(".md", message)
        self.assertIn(".txt", message)
        self.assertIn("10 MB", message)

    def test_rejects_unsupported_content_type(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.txt",
            b"document content",
            content_type="application/pdf",
        )

        with self.assertRaises(ValidationError) as error:
            validate_document_upload(uploaded_file)

        message = str(error.exception)
        self.assertIn(".md", message)
        self.assertIn(".txt", message)

    def test_rejects_file_larger_than_ten_megabytes(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.txt",
            b"x" * (10 * 1024 * 1024 + 1),
            content_type="text/plain",
        )

        with self.assertRaises(ValidationError) as error:
            validate_document_upload(uploaded_file)

        message = str(error.exception)
        self.assertIn("tamanho", message.lower())
        self.assertIn("10 MB", message)

    def test_accepts_file_at_exactly_ten_megabytes(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.txt",
            b"x" * (10 * 1024 * 1024),
            content_type="text/plain",
        )

        validate_document_upload(uploaded_file)
