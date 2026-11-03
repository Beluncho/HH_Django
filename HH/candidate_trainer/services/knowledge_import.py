"""Импорт документа в глобальную RAG-коллекцию.

Один путь для команды ``import_knowledge`` и для загрузки из админки: два входа
в одну и ту же базу знаний не должны расходиться в деталях — разбиении на
фрагменты, проверке размера или привязке к навыку.

Модуль существует потому, что ему нужны и ``services/knowledge``, и
``services/analysis`` (нормализация навыка): ``knowledge`` импортирует
``analysis``, поэтому обратная связь на уровне модулей была бы циклом.
"""

from pathlib import Path

from candidate_trainer.models import KnowledgeDocument

from .analysis import resolve_skill
from .embeddings import get_embedding_service
from .knowledge import (
    GLOBAL_COLLECTIONS,
    ensure_collection,
    index_imported_document,
    prepare_document_content,
)


def import_document(
    *,
    collection_slug,
    raw_bytes,
    filename,
    title="",
    source_type=KnowledgeDocument.SourceType.IMPORTED,
    source_url="",
    external_id="",
    normalized_skill=None,
    embedding_service=None,
):
    """Готовит файл и сохраняет его фрагменты в коллекцию.

    Оригинал файла не сохраняется: в метаданных остаётся только имя. Ошибки
    приходят как ``CandidateTrainerError`` (в том числе
    ``KnowledgeImportError`` и ``ReindexRequiredError``) — вызывающий код
    показывает их человеку.
    """
    config = GLOBAL_COLLECTIONS[collection_slug]
    content = prepare_document_content(raw_bytes, filename)
    embedding_service = embedding_service or get_embedding_service()
    collection = ensure_collection(
        slug=collection_slug,
        title=config["title"],
        kind=config["kind"],
        embedding_service=embedding_service,
    )
    skill = None
    if normalized_skill is not None:
        skill = resolve_skill(normalized_skill, embedding_service)
    return index_imported_document(
        collection=collection,
        title=title or Path(filename).stem,
        content=content,
        source_type=source_type,
        source_url=source_url,
        external_id=external_id,
        metadata={"filename": Path(filename).name},
        skill=skill,
        embedding_service=embedding_service,
    )
