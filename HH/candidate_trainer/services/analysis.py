import hashlib
import html
import re
from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags

from candidate_trainer.models import (
    AnalysisSkill,
    HHVacancySnapshot,
    Skill,
    VacancyAnalysis,
)

from .embeddings import get_embedding_service
from .exceptions import (
    AnalysisValidationError,
    CandidateTrainerError,
    HHAPIError,
    ReindexRequiredError,
)
from .hh_client import HHClient
from .knowledge import ensure_collection, index_vacancy_document
from .normalization import normalize_skill, normalize_vacancy_skills


def normalize_query(query):
    query = re.sub(r"\s+", " ", str(query or "")).strip()
    if len(query) < 2:
        raise AnalysisValidationError(
            "Название вакансии должно содержать минимум 2 символа"
        )
    if len(query) > 200:
        raise AnalysisValidationError(
            "Название вакансии не должно превышать 200 символов"
        )
    return query, query.casefold()


def create_or_get_analysis(*, user, query, area_id, area_name):
    query, normalized_query = normalize_query(query)
    area_id = str(area_id or "").strip()
    area_name = str(area_name or "").strip()
    if not area_id or not area_name:
        raise AnalysisValidationError("Выберите регион")

    cache_source = f"v1:{normalized_query}:{area_id}"
    cache_key = hashlib.sha256(cache_source.encode("utf-8")).hexdigest()
    defaults = {
        "query": query,
        "normalized_query": normalized_query,
        "area_id": area_id,
        "area_name": area_name,
    }
    try:
        analysis, created = VacancyAnalysis.objects.get_or_create(
            user=user,
            cache_key=cache_key,
            defaults=defaults,
        )
    except IntegrityError:
        analysis = VacancyAnalysis.objects.get(user=user, cache_key=cache_key)
        created = False
    return analysis, created


def _plain_text(value):
    value = re.sub(
        r"<\s*(br|/p|/li)\s*/?>",
        "\n",
        str(value or ""),
        flags=re.IGNORECASE,
    )
    value = html.unescape(strip_tags(value))
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _parsed_datetime(value):
    if not value:
        return None
    parsed = parse_datetime(value)
    return parsed


def _set_failed(analysis_id, message):
    VacancyAnalysis.objects.filter(pk=analysis_id).update(
        status=VacancyAnalysis.Status.FAILED,
        error_message=str(message)[:500],
        completed_at=timezone.now(),
    )


def resolve_skill(normalized, embedding_service):
    skill, _ = Skill.objects.get_or_create(
        normalized_name=normalized.key,
        defaults={"canonical_name": normalized.canonical_name},
    )
    if skill.embedding and (
        skill.embedding_model != embedding_service.model_name
        or skill.embedding_dimension != embedding_service.dimension
    ):
        raise ReindexRequiredError(
            f"Навык «{skill.canonical_name}» построен другой embedding-моделью. "
            "Запустите reindex_embeddings."
        )
    changed = []
    if not skill.embedding:
        skill.embedding = embedding_service.embed(skill.canonical_name)
        skill.embedding_model = embedding_service.model_name
        skill.embedding_dimension = embedding_service.dimension
        changed.extend(
            ["embedding", "embedding_model", "embedding_dimension", "updated_at"]
        )
    if skill.canonical_name != normalized.canonical_name:
        skill.canonical_name = normalized.canonical_name
        changed.extend(["canonical_name", "updated_at"])
    if changed:
        skill.save(update_fields=list(dict.fromkeys(changed)))
    return skill


def run_analysis(
    analysis_id,
    *,
    hh_client=None,
    embedding_service=None,
    force=False,
):
    hh_client = hh_client or HHClient()
    embedding_service = embedding_service or get_embedding_service()
    analysis = VacancyAnalysis.objects.select_related("user").get(pk=analysis_id)
    if analysis.status == VacancyAnalysis.Status.COMPLETED and not force:
        return analysis

    claimable = VacancyAnalysis.objects.filter(pk=analysis_id).exclude(
        status=VacancyAnalysis.Status.RUNNING,
    )
    if not force:
        claimable = claimable.exclude(
            status=VacancyAnalysis.Status.COMPLETED,
        )
    claimed = claimable.update(
        status=VacancyAnalysis.Status.RUNNING,
        error_message="",
        started_at=timezone.now(),
        completed_at=None,
    )
    if not claimed:
        analysis.refresh_from_db()
        if analysis.status == VacancyAnalysis.Status.COMPLETED and not force:
            return analysis
        raise CandidateTrainerError("Анализ уже выполняется")

    try:
        ensure_collection(
            slug="skill-core",
            title="База знаний по навыкам",
            kind="skill_core",
            embedding_service=embedding_service,
        )
        vacancy_ids = list(
            dict.fromkeys(
                str(external_id).strip()
                for external_id in hh_client.search_vacancy_ids(
                    analysis.query,
                    analysis.area_id,
                    limit=settings.HH_ANALYSIS_LIMIT,
                )
                if str(external_id).strip()
            )
        )
        cards_by_external_id = {}
        card_errors = 0
        for external_id in vacancy_ids:
            try:
                card = hh_client.get_vacancy(external_id)
            except HHAPIError:
                card_errors += 1
                continue
            card_id = str(card.external_id or external_id).strip()
            cards_by_external_id.setdefault(card_id, card)
        cards = list(cards_by_external_id.values())

        if vacancy_ids and not cards:
            raise HHAPIError("Не удалось получить ни одной полной карточки вакансии")

        with transaction.atomic():
            analysis = VacancyAnalysis.objects.select_for_update().get(pk=analysis_id)
            analysis.vacancies.clear()
            analysis.analysis_skills.all().delete()

            skill_stats = defaultdict(
                lambda: {
                    "count": 0,
                    "variants": set(),
                    "normalized": None,
                }
            )
            vacancy_skills = []

            for card in cards:
                snapshot, _ = HHVacancySnapshot.objects.update_or_create(
                    source="hh",
                    external_id=card.external_id,
                    defaults={
                        "title": card.title[:300],
                        "employer": card.employer[:300],
                        "url": card.url
                        or f"https://hh.ru/vacancy/{card.external_id}",
                        "published_at": _parsed_datetime(card.published_at),
                        "description": _plain_text(card.description),
                        "raw_skills": list(card.key_skills),
                    },
                )
                analysis.vacancies.add(snapshot)

                normalized_skills = normalize_vacancy_skills(card.key_skills)
                variants_by_key = defaultdict(set)
                for raw_skill in card.key_skills:
                    normalized_variant = normalize_skill(raw_skill)
                    if normalized_variant is not None:
                        variants_by_key[normalized_variant.key].add(
                            normalized_variant.variant
                        )
                resolved_skills = []
                for normalized in normalized_skills:
                    stats = skill_stats[normalized.key]
                    stats["count"] += 1
                    stats["variants"].update(variants_by_key[normalized.key])
                    stats["normalized"] = normalized
                    resolved_skills.append(
                        resolve_skill(normalized, embedding_service)
                    )
                vacancy_skills.append((snapshot, resolved_skills))

            ranked_stats = sorted(
                skill_stats.values(),
                key=lambda item: (
                    -item["count"],
                    item["normalized"].canonical_name.casefold(),
                ),
            )
            denominator = len(cards) or 1
            for rank, stats in enumerate(ranked_stats, start=1):
                skill = resolve_skill(
                    stats["normalized"],
                    embedding_service,
                )
                AnalysisSkill.objects.create(
                    analysis=analysis,
                    skill=skill,
                    vacancy_count=stats["count"],
                    frequency_percent=(
                        Decimal(stats["count"] * 100) / Decimal(denominator)
                    ).quantize(Decimal("0.01")),
                    rank=rank,
                    variants=sorted(stats["variants"], key=str.casefold),
                )

            for snapshot, skills in vacancy_skills:
                index_vacancy_document(
                    snapshot,
                    skills,
                    embedding_service=embedding_service,
                )

            analysis.status = VacancyAnalysis.Status.COMPLETED
            analysis.error_message = (
                f"Не удалось загрузить карточек: {card_errors}"
                if card_errors
                else ""
            )
            analysis.vacancies_found = len(vacancy_ids)
            analysis.vacancies_processed = len(cards)
            analysis.completed_at = timezone.now()
            analysis.save(
                update_fields=[
                    "status",
                    "error_message",
                    "vacancies_found",
                    "vacancies_processed",
                    "completed_at",
                    "updated_at",
                ]
            )
        return analysis
    except CandidateTrainerError as error:
        _set_failed(analysis_id, error)
        raise
    except Exception as error:
        message = "Не удалось завершить анализ вакансий"
        _set_failed(analysis_id, message)
        raise CandidateTrainerError(message) from error
