"""
Сервис для работы с глобальными объяснениями навыков
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from candidate_trainer.models import (
    SkillExplanation,
    KnowledgeCollection,
    LLMRequestLog,
)
from candidate_trainer.services.knowledge import KnowledgeRetriever, get_global_collection
from candidate_trainer.services.llm import get_llm_client
from candidate_trainer.services.llm_log import record_llm_call
from candidate_trainer.services.exceptions import RAGContextUnavailableError


# Период актуальности глобального объяснения (365 дней)
EXPLANATION_VALIDITY_DAYS = 365


def get_or_create_global_explanation(skill, *, user, force_refresh=False):
    """
    Получить или создать глобальное объяснение навыка.

    Логика:
    - Проверяется наличие активного глобального объяснения (user=NULL)
    - Если объяснению >= 365 дней, оно деактивируется и создаётся новое
    - Если force_refresh=True, принудительно создаётся новое

    Args:
        skill: экземпляр Skill
        user: пользователь, инициировавший запрос (для логирования)
        force_refresh: принудительно создать новое объяснение

    Returns:
        SkillExplanation (глобальное, is_active=True, user=NULL)
    """
    with transaction.atomic():
        # Ищем активное глобальное объяснение
        active_explanation = (
            SkillExplanation.objects
            .filter(skill=skill, user__isnull=True, is_active=True)
            .select_for_update()
            .first()
        )

        needs_update = False

        if active_explanation:
            age = timezone.now() - active_explanation.created_at
            if age > timedelta(days=EXPLANATION_VALIDITY_DAYS):
                needs_update = True
        else:
            needs_update = True

        if force_refresh:
            needs_update = True

        if needs_update:
            # Деактивируем старое
            if active_explanation:
                active_explanation.is_active = False
                active_explanation.save(update_fields=['is_active'])

            # Создаём новое
            new_explanation = _generate_explanation(skill, user=user)
            return new_explanation

        return active_explanation


def _generate_explanation(skill, *, user):
    """
    Сгенерировать новое объяснение через LLM и RAG.
    """
    retriever = KnowledgeRetriever()
    collection = get_global_collection(KnowledgeCollection.Kind.SKILL_CORE)

    contexts = retriever.retrieve(
        collection,
        skill.canonical_name,
        skill=skill,
        limit=5,
    )

    if not contexts:
        raise RAGContextUnavailableError(
            f"Для навыка «{skill.canonical_name}» пока нет содержательных фрагментов базы знаний"
        )

    llm_client = get_llm_client()

    # Формируем промт для объяснения
    system_prompt = (
        "Ты — эксперт по найму и развитию технических специалистов. "
        "Твоя задача — объяснить навык простым и структурированным языком."
    )

    context_text = "\n\n".join([
        f"Источник {i+1}:\n{ctx.content}"
        for i, ctx in enumerate(contexts)
    ])

    prompt_messages = [
        {
            "role": "user",
            "content": (
                f"Объясни навык «{skill.canonical_name}».\n\n"
                f"Контекст из базы знаний:\n{context_text}\n\n"
                "Структура ответа:\n"
                "1. Что это за навык\n"
                "2. Где применяется\n"
                "3. Ключевые аспекты владения\n"
                "4. Связанные технологии\n\n"
                "Ответ должен быть практичным и полезным для подготовки к собеседованию."
            )
        }
    ]

    with record_llm_call(
        LLMRequestLog.Operation.EXPLANATION,
        user=user,
        provider=llm_client.provider,
        model=llm_client.model,
    ) as call:
        response = call.remember(
            llm_client.complete(system_prompt, prompt_messages)
        )

    return SkillExplanation.objects.create(
        skill=skill,
        user=None,  # Глобальное объяснение
        is_active=True,
        content=response.text,
        sources=[context.as_source() for context in contexts],
        llm_provider=response.provider,
        llm_model=response.model,
    )
