from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from candidate_trainer.models import (
    KnowledgeChunk,
    KnowledgeCollection,
    Skill,
)
from candidate_trainer.services.embeddings import get_embedding_service
from candidate_trainer.services.exceptions import CandidateTrainerError


class Command(BaseCommand):
    help = "Явно перестраивает embeddings после смены модели или размерности."

    def add_arguments(self, parser):
        parser.add_argument(
            "--collection",
            choices=("all", "skill-core", "interview", "user-analytics"),
            default="all",
        )

    def handle(self, *args, **options):
        try:
            embedding_service = get_embedding_service()
            collection_name = options["collection"]
            if collection_name in {"all", "skill-core"}:
                self._reindex_skills(embedding_service)

            collections = KnowledgeCollection.objects.all()
            if collection_name != "all":
                collections = collections.filter(slug=collection_name)
            for collection in collections:
                self._reindex_collection(collection, embedding_service)
        except CandidateTrainerError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                "Переиндексация завершена: "
                f"{embedding_service.model_name} "
                f"({embedding_service.dimension})"
            )
        )

    def _reindex_skills(self, embedding_service):
        skills = list(Skill.objects.order_by("pk"))
        vectors = embedding_service.embed_many(
            [skill.canonical_name for skill in skills]
        )
        for skill, vector in zip(skills, vectors, strict=True):
            skill.embedding = vector
            skill.embedding_model = embedding_service.model_name
            skill.embedding_dimension = embedding_service.dimension
        if skills:
            Skill.objects.bulk_update(
                skills,
                ["embedding", "embedding_model", "embedding_dimension"],
            )

    def _reindex_collection(self, collection, embedding_service):
        chunks = list(
            KnowledgeChunk.objects.filter(
                document__collection=collection
            ).order_by("pk")
        )
        vectors = embedding_service.embed_many(
            [chunk.content for chunk in chunks]
        )
        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk.embedding = vector
            chunk.embedding_model = embedding_service.model_name
            chunk.embedding_dimension = embedding_service.dimension

        with transaction.atomic():
            if chunks:
                KnowledgeChunk.objects.bulk_update(
                    chunks,
                    ["embedding", "embedding_model", "embedding_dimension"],
                )
            collection.embedding_model = embedding_service.model_name
            collection.embedding_dimension = embedding_service.dimension
            collection.save(
                update_fields=[
                    "embedding_model",
                    "embedding_dimension",
                    "updated_at",
                ]
            )
