import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from candidate_trainer.models import KnowledgeCollection, KnowledgeDocument
from candidate_trainer.services.analysis import resolve_skill
from candidate_trainer.services.embeddings import get_embedding_service
from candidate_trainer.services.exceptions import CandidateTrainerError
from candidate_trainer.services.knowledge import (
    ensure_collection,
    index_imported_document,
)
from candidate_trainer.services.normalization import normalize_skill


COLLECTIONS = {
    "skill-core": {
        "title": "База знаний по навыкам",
        "kind": KnowledgeCollection.Kind.SKILL_CORE,
    },
    "interview": {
        "title": "База знаний для интервью",
        "kind": KnowledgeCollection.Kind.INTERVIEW,
    },
}


class Command(BaseCommand):
    help = "Импортирует txt, md или json документ в RAG-коллекцию."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument(
            "--collection",
            choices=COLLECTIONS,
            required=True,
        )
        parser.add_argument("--title")
        parser.add_argument("--source-url", default="")
        parser.add_argument("--external-id", default="")
        parser.add_argument("--skill")
        parser.add_argument(
            "--source-type",
            choices=(
                KnowledgeDocument.SourceType.IMPORTED,
                KnowledgeDocument.SourceType.VERIFIED,
                KnowledgeDocument.SourceType.GENERATED,
                KnowledgeDocument.SourceType.INTERVIEW,
            ),
            default=KnowledgeDocument.SourceType.IMPORTED,
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.is_file():
            raise CommandError(f"Файл не найден: {path}")
        if path.suffix.casefold() not in {".txt", ".md", ".json"}:
            raise CommandError("Поддерживаются только .txt, .md и .json")
        if path.stat().st_size > settings.KNOWLEDGE_IMPORT_MAX_BYTES:
            raise CommandError("Файл превышает допустимый размер")

        try:
            raw_content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise CommandError("Файл должен быть в кодировке UTF-8") from error

        if path.suffix.casefold() == ".json":
            try:
                payload = json.loads(raw_content)
            except json.JSONDecodeError as error:
                raise CommandError("JSON-файл содержит ошибку") from error
            if isinstance(payload, dict) and isinstance(payload.get("content"), str):
                content = payload["content"]
            else:
                content = json.dumps(payload, ensure_ascii=False, indent=2)
        else:
            content = raw_content
        if not content.strip():
            raise CommandError("Документ пуст")

        embedding_service = get_embedding_service()
        config = COLLECTIONS[options["collection"]]
        try:
            collection = ensure_collection(
                slug=options["collection"],
                title=config["title"],
                kind=config["kind"],
                embedding_service=embedding_service,
            )
            skill = None
            if options["skill"]:
                normalized = normalize_skill(options["skill"])
                if normalized is None:
                    raise CommandError("Не удалось нормализовать название навыка")
                skill = resolve_skill(normalized, embedding_service)
            document = index_imported_document(
                collection=collection,
                title=options["title"] or path.stem,
                content=content,
                source_type=options["source_type"],
                source_url=options["source_url"],
                external_id=options["external_id"],
                metadata={"filename": path.name},
                skill=skill,
                embedding_service=embedding_service,
            )
        except CandidateTrainerError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                f"Импортирован документ #{document.pk}: {document.title}"
            )
        )
