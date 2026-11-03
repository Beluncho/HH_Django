"""Общие помощники для демонстрационных management-команд.

Модуль лежит в пакете ``management``, но не в ``management/commands``,
поэтому Django не воспринимает его как команду.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.db import connection

from candidate_trainer.models import VacancyAnalysis
from candidate_trainer.services.embeddings import (
    HashEmbeddingService,
    SentenceTransformerEmbeddingService,
)

# Совпадает со значением EMBEDDING_MODEL в .env.local.example, чтобы модель
# называлась одинаково и при запуске через настройки, и при флаге --embedding.
HASH_MODEL_NAME = "local-hash-v1"
DEMO_USERNAME = "demo"
DEMO_EMAIL = "demo@example.com"


def ensure_database_ready():
    """Проверяет, что миграции приложения применены.

    Без этой проверки первое же обращение к базе падает OperationalError
    «no such table», и вместо результата в терминале оказывается трассировка.
    """
    table = VacancyAnalysis._meta.db_table
    if table not in connection.introspection.table_names():
        raise CommandError(
            "В базе нет таблиц candidate_trainer — миграции не применены. "
            "Выполните один раз: ./run_local.sh migrate"
        )


def write_run_header(command, *, query, area_id, area_name, user, embedding_service):
    """Печатает параметры прогона до обращения к HH API."""
    command.stdout.write(f"Запрос: {query}")
    command.stdout.write(f"Регион: {area_name} (area={area_id})")
    command.stdout.write(f"Пользователь: {user.username}")
    command.stdout.write(f"Embeddings: {embedding_service.model_name}")
    command.stdout.write(
        f"Ищу вакансии через HH API, беру до {settings.HH_ANALYSIS_LIMIT} шт. "
        "Это может занять до минуты..."
    )
    command.stdout.write("")


def resolve_area(area_id):
    """Возвращает (id, название) региона из settings.HH_AREA_CHOICES."""
    areas = dict(settings.HH_AREA_CHOICES)
    key = str(area_id or "").strip()
    if key not in areas:
        available = ", ".join(f"{item_id} — {name}" for item_id, name in settings.HH_AREA_CHOICES)
        raise CommandError(f"Неизвестный регион «{key}». Доступные: {available}")
    return key, areas[key]


def resolve_user(username=None):
    """Возвращает (пользователь, создан_ли). Без username берёт первого или создаёт demo."""
    user_model = get_user_model()
    if username:
        user = user_model.objects.filter(username=username).first()
        if user is None:
            raise CommandError(f"Пользователь «{username}» не найден")
        return user, False

    user = user_model.objects.order_by("pk").first()
    if user is not None:
        return user, False

    user = user_model.objects.create_user(
        username=DEMO_USERNAME,
        email=DEMO_EMAIL,
    )
    return user, True


def build_embedding_service(provider=None):
    """Собирает embedding-сервис, не изменяя настройки проекта."""
    provider = provider or settings.EMBEDDING_PROVIDER
    if provider == "hash":
        model_name = (
            settings.EMBEDDING_MODEL
            if settings.EMBEDDING_PROVIDER == "hash"
            else HASH_MODEL_NAME
        )
        return HashEmbeddingService(
            dimension=settings.EMBEDDING_DIMENSION,
            model_name=model_name,
        )
    if provider == "sentence_transformers":
        return SentenceTransformerEmbeddingService(
            model_name=settings.EMBEDDING_MODEL,
            dimension=settings.EMBEDDING_DIMENSION,
            device=settings.EMBEDDING_DEVICE,
            cache_dir=settings.EMBEDDING_CACHE_DIR,
        )
    raise CommandError(f"Неизвестный embedding provider: {provider}")


def parse_int_list(value, *, minimum=None, maximum=None):
    """Разбирает «3,4,6» в [3, 4, 6]."""
    result = []
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            number = int(part)
        except ValueError:
            raise CommandError(f"Ожидалось число, получено «{part}»") from None
        if minimum is not None and number < minimum:
            raise CommandError(f"Значение {number} меньше допустимого минимума {minimum}")
        if maximum is not None and number > maximum:
            raise CommandError(f"Значение {number} больше допустимого максимума {maximum}")
        result.append(number)
    if not result:
        raise CommandError("Пустой список значений")
    return result


def write_skill_table(command, analysis):
    """Печатает таблицу топ-навыков анализа."""
    rows = [
        (
            str(item.rank),
            item.skill.canonical_name,
            f"{item.vacancy_count}/{analysis.vacancies_processed or 0}",
            f"{item.frequency_percent:.2f}%",
            ", ".join(item.variants),
        )
        for item in analysis.analysis_skills.select_related("skill")
    ]
    if not rows:
        command.stdout.write("Навыки не найдены.")
        return

    table = [("РАНГ", "НАВЫК", "ВАКАНСИЙ", "ДОЛЯ", "ВАРИАНТЫ НАПИСАНИЯ")] + rows
    widths = [
        max(len(row[index]) for row in table)
        for index in range(len(table[0]))
    ]
    for row in table:
        line = "  ".join(
            cell.ljust(widths[index]) for index, cell in enumerate(row)
        )
        command.stdout.write(line.rstrip())


def write_sources(command, sources):
    """Печатает источники объяснения или найденных фрагментов."""
    if not sources:
        return
    command.stdout.write("Источники:")
    for source in sources:
        title = source.get("title") or source.get("external_id") or "без названия"
        url = source.get("url") or ""
        score = source.get("score")
        suffix = f" — {url}" if url else ""
        if score is not None:
            suffix += f" (score={score})"
        command.stdout.write(f"  - {title}{suffix}")
