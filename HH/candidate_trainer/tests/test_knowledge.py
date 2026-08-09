from django.test import TestCase

from candidate_trainer.models import (
    KnowledgeCollection,
    KnowledgeDocument,
    Skill,
)
from candidate_trainer.services.embeddings import HashEmbeddingService
from candidate_trainer.services.exceptions import ReindexRequiredError
from candidate_trainer.services.knowledge import (
    KnowledgeRetriever,
    ensure_collection,
    index_imported_document,
)


class KnowledgeRetrieverTest(TestCase):
    def setUp(self):
        self.embedding_service = HashEmbeddingService(
            dimension=12,
            model_name="test-hash-v1",
        )

    def create_collection(self):
        return ensure_collection(
            slug="skill-core",
            title="Навыки",
            kind=KnowledgeCollection.Kind.SKILL_CORE,
            embedding_service=self.embedding_service,
        )

    def test_empty_collection_returns_empty_context(self):
        collection = self.create_collection()

        result = KnowledgeRetriever(self.embedding_service).retrieve(
            collection,
            "Python",
        )

        self.assertEqual(result, [])

    def test_filled_collection_returns_content_and_provenance(self):
        collection = self.create_collection()
        skill = Skill.objects.create(
            canonical_name="Python",
            normalized_name="python",
        )
        index_imported_document(
            collection=collection,
            title="Python handbook",
            content=(
                "Python использует динамическую типизацию. "
                "Контекстный менеджер управляет ресурсами."
            ),
            source_type=KnowledgeDocument.SourceType.VERIFIED,
            source_url="https://docs.example/python",
            external_id="python-handbook",
            skill=skill,
            embedding_service=self.embedding_service,
        )

        result = KnowledgeRetriever(self.embedding_service).retrieve(
            collection,
            "контекстный менеджер Python",
            skill=skill,
        )

        self.assertEqual(len(result), 1)
        self.assertIn("Контекстный менеджер", result[0].content)
        self.assertEqual(result[0].source_type, "verified")
        self.assertEqual(result[0].source_url, "https://docs.example/python")

    def test_different_embedding_model_requires_reindex(self):
        collection = self.create_collection()
        other_service = HashEmbeddingService(
            dimension=12,
            model_name="another-model",
        )

        with self.assertRaises(ReindexRequiredError):
            KnowledgeRetriever(other_service).retrieve(
                collection,
                "Python",
            )
