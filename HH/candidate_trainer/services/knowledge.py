import hashlib
import math
import re
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from candidate_trainer.models import (
    HHVacancySnapshot,
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeDocument,
    Skill,
)

from .embeddings import get_embedding_service
from .exceptions import ReindexRequiredError


@dataclass(frozen=True)
class RetrievedContext:
    content: str
    score: float
    document_title: str
    source_type: str
    source_url: str
    external_id: str
    metadata: dict

    def as_source(self):
        return {
            "title": self.document_title,
            "source_type": self.source_type,
            "url": self.source_url,
            "external_id": self.external_id,
            "score": round(self.score, 4),
        }


def split_content(content, max_chars=900, overlap=120):
    content = re.sub(r"\r\n?", "\n", str(content or ""))
    content = re.sub(r"[ \t]+", " ", content)
    content = re.sub(r"\n{3,}", "\n\n", content).strip()
    if not content:
        return []

    chunks = []
    start = 0
    while start < len(content):
        end = min(start + max_chars, len(content))
        if end < len(content):
            boundary = max(
                content.rfind("\n", start + max_chars // 2, end),
                content.rfind(". ", start + max_chars // 2, end),
            )
            if boundary > start:
                end = boundary + 1
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(content):
            break
        start = max(end - overlap, start + 1)
    return chunks


def ensure_collection(
    *,
    slug,
    title,
    kind,
    owner=None,
    enabled=True,
    embedding_service=None,
):
    embedding_service = embedding_service or get_embedding_service()
    collection, _ = KnowledgeCollection.objects.get_or_create(
        owner=owner,
        slug=slug,
        defaults={
            "title": title,
            "kind": kind,
            "enabled": enabled,
            "embedding_model": embedding_service.model_name,
            "embedding_dimension": embedding_service.dimension,
        },
    )
    if (
        collection.embedding_model
        and (
            collection.embedding_model != embedding_service.model_name
            or collection.embedding_dimension != embedding_service.dimension
        )
    ):
        raise ReindexRequiredError(
            f"Коллекция «{collection.title}» построена другой embedding-моделью. "
            "Запустите reindex_embeddings."
        )
    changed_fields = []
    if not collection.embedding_model:
        collection.embedding_model = embedding_service.model_name
        changed_fields.append("embedding_model")
    if not collection.embedding_dimension:
        collection.embedding_dimension = embedding_service.dimension
        changed_fields.append("embedding_dimension")
    if collection.title != title:
        collection.title = title
        changed_fields.append("title")
    if collection.kind != kind:
        collection.kind = kind
        changed_fields.append("kind")
    if changed_fields:
        collection.save(update_fields=changed_fields + ["updated_at"])
    return collection


def index_vacancy_document(snapshot, skills, embedding_service=None):
    embedding_service = embedding_service or get_embedding_service()
    collection = ensure_collection(
        slug="skill-core",
        title="База знаний по навыкам",
        kind=KnowledgeCollection.Kind.SKILL_CORE,
        embedding_service=embedding_service,
    )

    description = snapshot.description.strip()
    if not description:
        names = ", ".join(snapshot.raw_skills)
        description = (
            f"Вакансия «{snapshot.title}» работодателя «{snapshot.employer}». "
            f"В карточке HH.ru перечислены требования к навыкам: {names or 'не указаны'}."
        )
    text_chunks = split_content(description)

    document, _ = KnowledgeDocument.objects.update_or_create(
        collection=collection,
        external_id=f"hh:{snapshot.external_id}",
        defaults={
            "title": snapshot.title,
            "source_type": KnowledgeDocument.SourceType.HH,
            "source_url": snapshot.url,
            "retrieved_at": snapshot.fetched_at,
            "metadata": {
                "employer": snapshot.employer,
                "published_at": (
                    snapshot.published_at.isoformat()
                    if snapshot.published_at
                    else None
                ),
                "skills": snapshot.raw_skills,
            },
        },
    )

    unique_contents = list(dict.fromkeys(text_chunks))
    vectors = embedding_service.embed_many(unique_contents)
    vectors_by_content = dict(zip(unique_contents, vectors, strict=True))

    chunks = []
    chunk_index = 0
    for skill in skills:
        for content in text_chunks:
            chunks.append(
                KnowledgeChunk(
                    document=document,
                    skill=skill,
                    chunk_index=chunk_index,
                    content=content,
                    content_hash=hashlib.sha256(
                        content.encode("utf-8")
                    ).hexdigest(),
                    embedding=vectors_by_content[content],
                    embedding_model=embedding_service.model_name,
                    embedding_dimension=embedding_service.dimension,
                    metadata={"source": "hh", "external_id": snapshot.external_id},
                )
            )
            chunk_index += 1

    with transaction.atomic():
        document.chunks.all().delete()
        KnowledgeChunk.objects.bulk_create(chunks)
    return document


def index_imported_document(
    *,
    collection,
    title,
    content,
    source_type,
    source_url="",
    external_id="",
    metadata=None,
    skill=None,
    embedding_service=None,
):
    embedding_service = embedding_service or get_embedding_service()
    if (
        collection.embedding_model != embedding_service.model_name
        or collection.embedding_dimension != embedding_service.dimension
    ):
        raise ReindexRequiredError(
            f"Коллекция «{collection.title}» требует переиндексации"
        )
    text_chunks = split_content(content)
    vectors = embedding_service.embed_many(text_chunks)

    document = KnowledgeDocument.objects.create(
        collection=collection,
        title=title,
        source_type=source_type,
        source_url=source_url,
        external_id=external_id,
        retrieved_at=timezone.now(),
        metadata=metadata or {},
    )
    KnowledgeChunk.objects.bulk_create(
        [
            KnowledgeChunk(
                document=document,
                skill=skill,
                chunk_index=index,
                content=chunk,
                content_hash=hashlib.sha256(chunk.encode("utf-8")).hexdigest(),
                embedding=vector,
                embedding_model=embedding_service.model_name,
                embedding_dimension=embedding_service.dimension,
                metadata=metadata or {},
            )
            for index, (chunk, vector) in enumerate(
                zip(text_chunks, vectors, strict=True)
            )
        ]
    )
    return document


def _cosine_similarity(left, right):
    if len(left) != len(right) or not left:
        return -1.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return -1.0
    return numerator / (left_norm * right_norm)


class KnowledgeRetriever:
    def __init__(self, embedding_service=None):
        self.embedding_service = embedding_service or get_embedding_service()

    def retrieve(self, collection, query, *, skill=None, limit=5):
        if not collection or not collection.enabled:
            return []
        if (
            collection.embedding_model != self.embedding_service.model_name
            or collection.embedding_dimension != self.embedding_service.dimension
        ):
            raise ReindexRequiredError(
                f"Коллекция «{collection.title}» требует переиндексации"
            )

        chunks = KnowledgeChunk.objects.filter(
            document__collection=collection,
            embedding_model=self.embedding_service.model_name,
            embedding_dimension=self.embedding_service.dimension,
        ).select_related("document")
        if skill is not None:
            chunks = chunks.filter(Q(skill=skill) | Q(skill__isnull=True))

        query_vector = self.embedding_service.embed(query)
        ranked = sorted(
            (
                (_cosine_similarity(query_vector, chunk.embedding), chunk)
                for chunk in chunks.iterator()
                if chunk.embedding
            ),
            key=lambda item: item[0],
            reverse=True,
        )[:limit]
        return [
            RetrievedContext(
                content=chunk.content,
                score=score,
                document_title=chunk.document.title,
                source_type=chunk.document.source_type,
                source_url=chunk.document.source_url,
                external_id=chunk.document.external_id,
                metadata=chunk.document.metadata,
            )
            for score, chunk in ranked
        ]


def get_global_collection(kind):
    return KnowledgeCollection.objects.filter(
        owner__isnull=True,
        kind=kind,
        enabled=True,
    ).first()


def get_skill_by_name(name):
    return Skill.objects.filter(normalized_name=name).first()
