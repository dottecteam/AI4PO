import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadhandler import StopUpload
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Documento, Projeto
from .upload_handlers import DocumentUploadSizeHandler
from .validators import MAX_UPLOAD_SIZE_BYTES, validate_document_upload


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


class DocumentUploadSizeHandlerTests(SimpleTestCase):
    def test_stops_stream_after_ten_megabytes(self):
        request = SimpleNamespace()
        handler = DocumentUploadSizeHandler(request)
        allowed_chunk = b"x" * MAX_UPLOAD_SIZE_BYTES

        self.assertEqual(handler.receive_data_chunk(allowed_chunk, 0), allowed_chunk)
        with self.assertRaises(StopUpload):
            handler.receive_data_chunk(b"x", MAX_UPLOAD_SIZE_BYTES)

        self.assertTrue(request.document_upload_too_large)


class DocumentoFilePersistenceTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)

        media_override = override_settings(MEDIA_ROOT=self.media_root)
        media_override.enable()
        self.addCleanup(media_override.disable)

        usuario_po = get_user_model().objects.create_user(username="product-owner")
        self.projeto = Projeto.objects.create(
            usuario_po=usuario_po,
            nome="Projeto de testes",
            descricao="Descrição",
            objetivo="Objetivo",
        )

    def test_saves_uploaded_file_in_configured_storage(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.txt",
            b"conteudo do documento",
            content_type="text/plain",
        )

        documento = Documento.objects.create(
            projeto=self.projeto,
            nome=uploaded_file.name,
            tipo="txt",
            arquivo=uploaded_file,
        )

        self.assertTrue(documento.arquivo.name.startswith("uploads/"))
        self.assertTrue(documento.arquivo.storage.exists(documento.arquivo.name))
        with documento.arquivo.open("rb") as stored_file:
            self.assertEqual(stored_file.read(), b"conteudo do documento")

    def test_keeps_file_optional_for_legacy_document_metadata(self):
        arquivo_field = Documento._meta.get_field("arquivo")

        self.assertTrue(arquivo_field.blank)
        documento = Documento.objects.create(
            projeto=self.projeto,
            nome="Documento anterior à rota de upload",
            tipo="txt",
        )
        self.assertFalse(documento.arquivo)


class DocumentUploadAPITests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)

        media_override = override_settings(MEDIA_ROOT=self.media_root)
        media_override.enable()
        self.addCleanup(media_override.disable)

        usuario_po = get_user_model().objects.create_user(username="api-product-owner")
        self.projeto = Projeto.objects.create(
            usuario_po=usuario_po,
            nome="Projeto da API",
            descricao="Descrição",
            objetivo="Objetivo",
        )
        self.client = APIClient()
        self.url = reverse("document-upload", kwargs={"project_id": self.projeto.pk})

    def test_uploads_supported_document_and_returns_created_metadata(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.txt",
            b"conteudo enviado pela API",
            content_type="text/plain",
        )

        with patch('projects.views.indexar_documento') as mock_indexar:
            response = self.client.post(
                self.url,
                {"arquivo": uploaded_file},
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        documento = Documento.objects.get()
        mock_indexar.assert_called_once_with(documento)
        self.assertEqual(documento.estado, 'processado')
        self.assertEqual(documento.projeto, self.projeto)
        self.assertEqual(documento.nome, "requirements.txt")
        self.assertEqual(documento.tipo, "txt")
        self.assertEqual(response.data["id"], documento.pk)
        self.assertEqual(response.data["projeto"], self.projeto.pk)
        self.assertEqual(response.data["nome"], "requirements.txt")
        self.assertEqual(response.data["tipo"], "txt")
        self.assertEqual(response.data["estado"], "processado")
        self.assertTrue(
            response.data["arquivo"].endswith("/media/uploads/requirements.txt")
        )
        self.assertIn("data", response.data)
        self.assertTrue(documento.arquivo.storage.exists(documento.arquivo.name))

    def test_rejects_request_without_a_file(self):
        response = self.client.post(self.url, {}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("arquivo", response.data)
        self.assertFalse(Documento.objects.exists())

    def test_rejects_unsupported_document(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.pdf",
            b"conteudo invalido",
            content_type="application/pdf",
        )

        response = self.client.post(
            self.url,
            {"arquivo": uploaded_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        message = str(response.data["arquivo"][0])
        self.assertIn(".md", message)
        self.assertIn(".txt", message)
        self.assertIn("10 MB", message)
        self.assertFalse(Documento.objects.exists())

    def test_rejects_document_larger_than_ten_megabytes(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.txt",
            b"x" * (10 * 1024 * 1024 + 1),
            content_type="text/plain",
        )

        response = self.client.post(
            self.url,
            {"arquivo": uploaded_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("10 MB", str(response.data["arquivo"][0]))
        self.assertFalse(Documento.objects.exists())

    def test_accepts_document_at_exactly_ten_megabytes(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.txt",
            b"x" * MAX_UPLOAD_SIZE_BYTES,
            content_type="text/plain",
        )

        with patch('projects.views.indexar_documento'):
            response = self.client.post(
                self.url,
                {"arquivo": uploaded_file},
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Documento.objects.exists())

    def test_rejects_clearly_oversized_request_before_parsing_it(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.txt",
            b"x" * (11 * 1024 * 1024),
            content_type="text/plain",
        )

        with patch.object(
            DocumentUploadSizeHandler,
            "receive_data_chunk",
            side_effect=AssertionError("O corpo não deveria ser processado"),
        ):
            response = self.client.post(
                self.url,
                {"arquivo": uploaded_file},
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("10 MB", str(response.data["arquivo"][0]))
        self.assertFalse(Documento.objects.exists())

    def test_returns_not_found_for_unknown_project(self):
        uploaded_file = SimpleUploadedFile(
            "requirements.md",
            b"conteudo",
            content_type="text/markdown",
        )
        unknown_project_url = reverse(
            "document-upload",
            kwargs={"project_id": self.projeto.pk + 999},
        )

        response = self.client.post(
            unknown_project_url,
            {"arquivo": uploaded_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Documento.objects.exists())

    def test_estado_vira_erro_quando_extração_falha(self):
        from ai.extraction import ArquivoNaoEncontradoError

        uploaded_file = SimpleUploadedFile(
            "requirements.txt",
            b"conteudo",
            content_type="text/plain",
        )

        with patch('ai.indexing.extrair_texto',
                   side_effect=ArquivoNaoEncontradoError('arquivo sumiu')):
            response = self.client.post(
                self.url,
                {"arquivo": uploaded_file},
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        documento = Documento.objects.get()
        self.assertEqual(documento.estado, 'erro')
        self.assertTrue(documento.mensagem_erro)

    def test_estado_vira_erro_quando_embedding_falha(self):
        from ai.indexing import FalhaDeEmbeddingError

        uploaded_file = SimpleUploadedFile(
            "requirements.txt",
            b"conteudo",
            content_type="text/plain",
        )

        with patch('ai.indexing.gerar_embeddings',
                   side_effect=FalhaDeEmbeddingError('ollama fora')):
            response = self.client.post(
                self.url,
                {"arquivo": uploaded_file},
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        documento = Documento.objects.get()
        self.assertEqual(documento.estado, 'erro')
        self.assertTrue(documento.mensagem_erro)