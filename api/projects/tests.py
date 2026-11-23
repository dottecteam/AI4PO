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

        usuario_po = get_user_model().objects.create_user(
            email="po@test.com",
            nome="Product Owner",
        )
        self.projeto = Projeto.objects.create(
            usuario_po=usuario_po,
            titulo="Projeto de testes",
            descricao="Descrição",
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

        usuario_po = get_user_model().objects.create_user(
            email="api-po@test.com",
            nome="API Product Owner",
        )
        self.projeto = Projeto.objects.create(
            usuario_po=usuario_po,
            titulo="Projeto da API",
            descricao="Descrição",
        )
        self.client = APIClient()
        # As rotas exigem IsAuthenticated; sem isto todo request volta 401.
        self.client.force_authenticate(usuario_po)
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


class DocumentReprocessAPITests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)

        media_override = override_settings(MEDIA_ROOT=self.media_root)
        media_override.enable()
        self.addCleanup(media_override.disable)

        usuario_po = get_user_model().objects.create_user(
            email="reprocess-po@test.com",
            nome="Reprocess PO",
        )
        self.projeto = Projeto.objects.create(
            usuario_po=usuario_po,
            titulo="Projeto Reprocessamento",
            descricao="Descrição",
        )
        self.client = APIClient()
        # Mesmo caso do upload: a rota e protegida, o cliente precisa de identidade.
        self.client.force_authenticate(usuario_po)

        self.uploaded_file = SimpleUploadedFile(
            "documento_falho.txt",
            b"conteudo do documento falho",
            content_type="text/plain",
        )
        self.documento = Documento.objects.create(
            projeto=self.projeto,
            nome="documento_falho.txt",
            tipo="txt",
            arquivo=self.uploaded_file,
            estado="erro",
            mensagem_erro="Falha de embedding anterior",
        )
        self.url = reverse(
            "document-reprocess",
            kwargs={
                "project_id": self.projeto.pk,
                "document_id": self.documento.pk,
            },
        )

    def test_reprocessa_documento_com_sucesso(self):
        with patch('projects.views.indexar_documento') as mock_indexar:
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.documento.refresh_from_db()
        mock_indexar.assert_called_once_with(self.documento)
        self.assertEqual(self.documento.estado, "processado")
        self.assertEqual(self.documento.mensagem_erro, "")
        self.assertEqual(response.data["id"], self.documento.pk)
        self.assertEqual(response.data["estado"], "processado")
        self.assertEqual(response.data["mensagem_erro"], "")

    def test_reprocessa_limpa_chunks_antigos_antes_de_reindexar(self):
        from ai.models import ChunkDoc

        # Simula chunks que ficaram salvos de uma tentativa anterior
        ChunkDoc.objects.create(
            documento=self.documento,
            projeto=self.projeto,
            conteudo="chunk antigo",
            embedding=[0.1] * 768,
        )
        self.assertEqual(self.documento.chunks.count(), 1)

        with patch('projects.views.indexar_documento'):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # O mock de indexar_documento não cria chunks novos, então deve restar 0 chunks
        self.assertEqual(self.documento.chunks.count(), 0)

    def test_reprocessa_falha_de_embedding_atualiza_estado_e_mensagem(self):
        from ai.indexing import FalhaDeEmbeddingError

        with patch(
            'projects.views.indexar_documento',
            side_effect=FalhaDeEmbeddingError("Ollama fora do ar"),
        ):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.documento.refresh_from_db()
        self.assertEqual(self.documento.estado, "erro")
        self.assertIn("Ollama fora do ar", self.documento.mensagem_erro)
        self.assertEqual(response.data["estado"], "erro")

    def test_reprocessa_falha_de_extracao_atualiza_estado_e_mensagem(self):
        from ai.extraction import ArquivoNaoEncontradoError

        with patch(
            'projects.views.indexar_documento',
            side_effect=ArquivoNaoEncontradoError("Arquivo físico não encontrado"),
        ):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.documento.refresh_from_db()
        self.assertEqual(self.documento.estado, "erro")
        self.assertIn("Arquivo físico não encontrado", self.documento.mensagem_erro)
        self.assertEqual(response.data["estado"], "erro")

    def test_reprocessa_retorna_404_para_documento_inexistente(self):
        url_inexistente = reverse(
            "document-reprocess",
            kwargs={
                "project_id": self.projeto.pk,
                "document_id": self.documento.pk + 999,
            },
        )
        response = self.client.post(url_inexistente)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reprocessa_retorna_404_para_documento_de_outro_projeto(self):
        outro_projeto = Projeto.objects.create(
            usuario_po=self.projeto.usuario_po,
            titulo="Outro Projeto",
            descricao="Outra Descrição",
        )
        url_outro_projeto = reverse(
            "document-reprocess",
            kwargs={
                "project_id": outro_projeto.pk,
                "document_id": self.documento.pk,
            },
        )
        response = self.client.post(url_outro_projeto)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reprocessa_documento_sem_arquivo_retorna_400(self):
        doc_sem_arquivo = Documento.objects.create(
            projeto=self.projeto,
            nome="sem_arquivo.txt",
            tipo="txt",
            estado="erro",
        )
        url_sem_arquivo = reverse(
            "document-reprocess",
            kwargs={
                "project_id": self.projeto.pk,
                "document_id": doc_sem_arquivo.pk,
            },
        )
        response = self.client.post(url_sem_arquivo)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_reprocessa_documento_ja_em_processamento_retorna_409(self):
        self.documento.estado = "processando"
        self.documento.save(update_fields=["estado"])

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error", response.data)


class EscopoEntrePOsTests(TestCase):
    """Prova a regra da historia #1: cada PO so enxerga os proprios projetos.

    Antes de `users.permissions.escopo` entrar em projects/views.py, todos os
    casos abaixo devolviam os dados alheios com 200 -- inclusive o DELETE, que
    apagava em cascata documentos, chunks e grafo de outro PO. Falham de
    proposito se o filtro for removido.
    """

    def setUp(self):
        User = get_user_model()
        self.dono = User.objects.create_user(
            email="dono-escopo@test.com", nome="Dono")
        self.intruso = User.objects.create_user(
            email="intruso-escopo@test.com", nome="Intruso")
        self.projeto = Projeto.objects.create(
            usuario_po=self.dono,
            titulo="Projeto do Dono",
            descricao="nada a ver com o intruso",
        )
        self.documento = Documento.objects.create(
            projeto=self.projeto, nome="requisitos.md", tipo="md")
        self.client = APIClient()
        self.client.force_authenticate(self.intruso)

    def test_lista_devolve_so_os_projetos_de_quem_logou(self):
        resposta = self.client.get(reverse("projeto-list-create"))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.json(), [])

    def test_nao_le_projeto_alheio(self):
        resposta = self.client.get(
            reverse("projeto_detail", args=[self.projeto.pk]))
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_nao_edita_projeto_alheio(self):
        resposta = self.client.patch(
            reverse("projeto_detail", args=[self.projeto.pk]),
            {"titulo": "sequestrado"},
            format="json",
        )
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
        self.projeto.refresh_from_db()
        self.assertEqual(self.projeto.titulo, "Projeto do Dono")

    def test_nao_apaga_projeto_alheio(self):
        resposta = self.client.delete(
            reverse("projeto_detail", args=[self.projeto.pk]))
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Projeto.objects.filter(pk=self.projeto.pk).exists())
        # nada em cascata foi tocado
        self.assertTrue(Documento.objects.filter(pk=self.documento.pk).exists())

    def test_idPo_no_corpo_nao_muda_a_posse(self):
        """idPo passou a read_only: o dono e sempre quem esta logado."""
        resposta = self.client.post(
            reverse("projeto-list-create"),
            {"titulo": "Novo", "descricao": "x",
             "status": "Rascunho", "idPo": self.dono.pk},
            format="json",
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        criado = Projeto.objects.get(titulo="Novo")
        self.assertEqual(criado.usuario_po_id, self.intruso.pk)

    def test_nao_envia_documento_para_projeto_alheio(self):
        arquivo = SimpleUploadedFile(
            "invasao.md", b"conteudo", content_type="text/markdown")
        resposta = self.client.post(
            reverse("document-upload", kwargs={"project_id": self.projeto.pk}),
            {"arquivo": arquivo},
            format="multipart",
        )
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Documento.objects.filter(projeto=self.projeto).count(), 1)

    def test_nao_reprocessa_documento_alheio(self):
        resposta = self.client.post(
            reverse(
                "document-reprocess",
                kwargs={"project_id": self.projeto.pk,
                        "document_id": self.documento.pk},
            )
        )
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_nao_apaga_documento_alheio(self):
        resposta = self.client.delete(
            reverse(
                "document-delete",
                kwargs={"project_id": self.projeto.pk,
                        "document_id": self.documento.pk},
            )
        )
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Documento.objects.filter(pk=self.documento.pk).exists())

    def test_listar_documentos_alheios_devolve_lista_vazia(self):
        """A rota e aninhada por projeto; o escopo deixa o resultado vazio."""
        resposta = self.client.get(
            reverse("document-list", kwargs={"project_id": self.projeto.pk}))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.json(), [])

    def test_dono_continua_enxergando_o_proprio_projeto(self):
        self.client.force_authenticate(self.dono)
        self.assertEqual(
            self.client.get(reverse("projeto_detail", args=[self.projeto.pk])).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            len(self.client.get(reverse("projeto-list-create")).json()), 1)