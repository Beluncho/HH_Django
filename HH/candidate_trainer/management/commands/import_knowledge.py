from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from candidate_trainer.models import KnowledgeDocument
from candidate_trainer.services.exceptions import CandidateTrainerError
from candidate_trainer.services.knowledge import GLOBAL_COLLECTIONS
from candidate_trainer.services.knowledge_import import import_document
from candidate_trainer.services.normalization import normalize_skill


class Command(BaseCommand):
    help = "Импортирует txt, md или json документ в RAG-коллекцию."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument(
            "--collection",
            choices=GLOBAL_COLLECTIONS,
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

        normalized_skill = None
        if options["skill"]:
            normalized_skill = normalize_skill(options["skill"])
            if normalized_skill is None:
                raise CommandError("Не удалось нормализовать название навыка")

        try:
            document = import_document(
                collection_slug=options["collection"],
                raw_bytes=path.read_bytes(),
                filename=path.name,
                title=options["title"] or "",
                source_type=options["source_type"],
                source_url=options["source_url"],
                external_id=options["external_id"],
                normalized_skill=normalized_skill,
            )
        except CandidateTrainerError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                f"Импортирован документ #{document.pk}: {document.title}"
            )
        )
