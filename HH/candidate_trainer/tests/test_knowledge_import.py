from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from candidate_trainer.models import (
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeDocument,
)
from candidate_trainer.services.exceptions import KnowledgeImportError
from candidate_trainer.services.knowledge import prepare_document_content
from userapp.models import WebSiteUser


class PrepareDocumentContentTest(SimpleTestCase):
    def test_plain_text_is_returned_as_is(self):
        content = prepare_document_content(
            "# Методика\n\nЗадавайте по одному вопросу.".encode("utf-8"),
            "method.md",
        )

        self.assertIn("Задавайте по одному вопросу", content)

    def test_unsupported_extension_is_rejected(self):
        with self.assertRaisesMessage(KnowledgeImportError, ".txt, .md"):
            prepare_document_content(b"content", "method.pdf")

    def test_oversized_file_is_rejected(self):
        with self.assertRaisesMessage(KnowledgeImportError, "размер"):
            prepare_document_content(b"x" * 20, "method.md", max_bytes=10)

    def test_broken_encoding_is_rejected(self):
        with self.assertRaisesMessage(KnowledgeImportError, "UTF-8"):
            prepare_document_content(b"\xff\xfe\x00bad", "method.md")

    def test_empty_document_is_rejected(self):
        with self.assertRaisesMessage(KnowledgeImportError, "пуст"):
            prepare_document_content("   \n\n ".encode("utf-8"), "method.md")

    def test_json_with_content_key_is_unwrapped(self):
        raw = '{"content": "Вопросы и рубрики"}'

        content = prepare_document_content(raw.encode("utf-8"), "method.json")

        self.assertEqual(content, "Вопросы и рубрики")

    def test_json_without_content_key_is_dumped(self):
        raw = '{"questions": ["Первый"], "tone": "спокойный"}'

        content = prepare_document_content(raw.encode("utf-8"), "method.json")

        self.assertIn('"questions"', content)
        self.assertIn("Первый", content)

    def test_broken_json_is_rejected(self):
        with self.assertRaisesMessage(KnowledgeImportError, "JSON"):
            prepare_document_content(b'{"content": ', "method.json")


class KnowledgeImportAdminTest(TestCase):
    def setUp(self):
        self.admin_user = WebSiteUser.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)
        self.url = reverse("admin:candidate_trainer_knowledge_import")

    def upload(self, content, filename="method.md", **overrides):
        if isinstance(content, str):
            content = content.encode("utf-8")
        payload = {
            "collection": "interview",
            "source_type": KnowledgeDocument.SourceType.INTERVIEW,
            "title": "Методика собеседования",
            "source_url": "",
            "skill": "",
        }
        payload.update(overrides)
        return self.client.post(
            self.url,
            {
                **payload,
                "file": SimpleUploadedFile(
                    filename,
                    content,
                    content_type="text/markdown",
                ),
            },
        )

    @override_settings(
        EMBEDDING_PROVIDER="hash",
        EMBEDDING_MODEL="local-hash-v1",
    )
    def test_uploaded_document_is_chunked_and_vectorised(self):
        response = self.upload(
            (
                "Собеседование идёт по одному вопросу за раз. "
                "Сначала проверяем базовые понятия, затем практику. "
            )
            * 40
        )

        self.assertRedirects(
            response,
            reverse("admin:candidate_trainer_knowledgecollection_changelist"),
        )
        document = KnowledgeDocument.objects.get()
        self.assertEqual(document.collection.slug, "interview")
        self.assertEqual(document.metadata["filename"], "method.md")
        self.assertGreater(document.chunks.count(), 1)
        for chunk in document.chunks.all():
            self.assertTrue(chunk.embedding)
            self.assertEqual(len(chunk.content_hash), 64)
            self.assertEqual(chunk.embedding_model, "local-hash-v1")

    @override_settings(
        EMBEDDING_PROVIDER="hash",
        EMBEDDING_MODEL="local-hash-v1",
    )
    def test_collection_built_by_another_model_reports_form_error(self):
        KnowledgeCollection.objects.create(
            owner=None,
            slug="interview",
            title="База знаний для интервью",
            kind=KnowledgeCollection.Kind.INTERVIEW,
            embedding_model="another-model",
            embedding_dimension=99,
        )

        response = self.upload("Текст методички")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "reindex_embeddings")
        self.assertFalse(KnowledgeDocument.objects.exists())
        self.assertFalse(KnowledgeChunk.objects.exists())

    @override_settings(
        EMBEDDING_PROVIDER="hash",
        EMBEDDING_MODEL="local-hash-v1",
    )
    def test_unsupported_file_reports_form_error(self):
        response = self.upload(b"not a text file", filename="method.pdf")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ".txt, .md")
        self.assertFalse(KnowledgeDocument.objects.exists())

    @override_settings(
        EMBEDDING_PROVIDER="hash",
        EMBEDDING_MODEL="local-hash-v1",
    )
    def test_import_requires_staff_permission(self):
        self.client.logout()
        stranger = WebSiteUser.objects.create_user(
            username="stranger",
            email="stranger@example.com",
            password="test-password",
        )
        self.client.force_login(stranger)

        response = self.upload("Текст методички")

        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(KnowledgeDocument.objects.exists())

    def test_changelist_offers_link_to_import_page(self):
        response = self.client.get(
            reverse("admin:candidate_trainer_knowledgecollection_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.url)
