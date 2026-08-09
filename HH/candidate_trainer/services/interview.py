import json
import re

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from candidate_trainer.models import (
    AnalysisSkill,
    InterviewInsight,
    InterviewMessage,
    InterviewSession,
    KnowledgeCollection,
    KnowledgeDocument,
    SkillExplanation,
    VacancyAnalysis,
)

from .embeddings import get_embedding_service
from .exceptions import (
    CandidateTrainerError,
    InterviewStateError,
    LLMError,
    RAGContextUnavailableError,
)
from .knowledge import (
    KnowledgeRetriever,
    ensure_collection,
    get_global_collection,
    index_imported_document,
)
from .llm import get_llm_client
from .prompts import (
    evaluation_prompt,
    explanation_prompt,
    initial_question_prompt,
)


def _next_sequence(session):
    maximum = session.messages.aggregate(value=Max("sequence"))["value"]
    return (maximum or 0) + 1


def explain_skill(
    analysis_skill,
    *,
    user,
    llm_client=None,
    retriever=None,
):
    if analysis_skill.analysis.user_id != user.id:
        raise InterviewStateError("Анализ недоступен")
    if analysis_skill.analysis.status != VacancyAnalysis.Status.COMPLETED:
        raise InterviewStateError("Анализ ещё не завершён")

    retriever = retriever or KnowledgeRetriever()
    collection = get_global_collection(KnowledgeCollection.Kind.SKILL_CORE)
    contexts = retriever.retrieve(
        collection,
        analysis_skill.skill.canonical_name,
        skill=analysis_skill.skill,
        limit=5,
    )
    if not contexts:
        raise RAGContextUnavailableError(
            "Для этого навыка пока нет содержательных фрагментов базы знаний"
        )

    llm_client = llm_client or get_llm_client()
    system_prompt, prompt_messages = explanation_prompt(
        analysis_skill,
        contexts,
    )
    response = llm_client.complete(system_prompt, prompt_messages)
    return SkillExplanation.objects.create(
        user=user,
        analysis_skill=analysis_skill,
        content=response.text,
        sources=[context.as_source() for context in contexts],
        llm_provider=response.provider,
        llm_model=response.model,
    )


def start_interview(*, analysis, user):
    if analysis.user_id != user.id:
        raise InterviewStateError("Анализ недоступен")
    if analysis.status != VacancyAnalysis.Status.COMPLETED:
        raise InterviewStateError("Сначала завершите анализ вакансий")
    first_skill = (
        analysis.analysis_skills.select_related("skill")
        .order_by("rank")
        .first()
    )
    if first_skill is None:
        raise InterviewStateError(
            "В анализе нет навыков для проведения собеседования"
        )
    return InterviewSession.objects.create(
        user=user,
        analysis=analysis,
        current_skill=first_skill.skill,
        interview_rag_enabled=settings.INTERVIEW_RAG_ENABLED,
    )


def _interview_contexts(session, query, retriever):
    if not session.interview_rag_enabled:
        return []
    collection = get_global_collection(KnowledgeCollection.Kind.INTERVIEW)
    if collection is None or not collection.documents.exists():
        return []
    return retriever.retrieve(collection, query, limit=4)


def ensure_initial_question(
    session,
    *,
    user,
    llm_client=None,
    retriever=None,
):
    if session.user_id != user.id:
        raise InterviewStateError("Собеседование недоступно")
    existing = session.messages.order_by("sequence").first()
    if existing is not None:
        return existing

    analysis_skills = list(
        session.analysis.analysis_skills.select_related("skill").order_by("rank")[:8]
    )
    skills = [item.skill for item in analysis_skills]
    retriever = retriever or KnowledgeRetriever()
    contexts = _interview_contexts(
        session,
        session.current_skill.canonical_name,
        retriever,
    )
    system_prompt, prompt_messages = initial_question_prompt(
        session.analysis,
        skills,
        contexts,
    )
    response = (llm_client or get_llm_client()).complete(
        system_prompt,
        prompt_messages,
    )
    with transaction.atomic():
        locked = InterviewSession.objects.select_for_update().get(pk=session.pk)
        existing = locked.messages.order_by("sequence").first()
        if existing is not None:
            return existing
        return InterviewMessage.objects.create(
            session=locked,
            role=InterviewMessage.Role.ASSISTANT,
            content=response.text,
            skill=locked.current_skill,
            sequence=1,
            metadata={
                "question": response.text,
                "llm_provider": response.provider,
                "llm_model": response.model,
            },
        )


def _parse_evaluation(text):
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        payload = json.loads(cleaned)
    except (TypeError, json.JSONDecodeError) as error:
        raise LLMError("LLM вернул некорректную структуру оценки") from error
    if not isinstance(payload, dict):
        raise LLMError("LLM вернул некорректную структуру оценки")

    scores = {}
    for field in ("correctness", "depth", "practical_application"):
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
            raise LLMError("LLM вернул оценку вне допустимой рубрики")
        scores[field] = value

    def string_list(field):
        value = payload.get(field)
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise LLMError("LLM вернул некорректную структуру оценки")
        return [item.strip() for item in value if item.strip()][:10]

    for field in ("summary", "feedback", "next_question"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise LLMError("LLM вернул неполную структуру оценки")

    return {
        **scores,
        "gaps": string_list("gaps"),
        "recommendations": string_list("recommendations"),
        "summary": payload["summary"].strip(),
        "feedback": payload["feedback"].strip(),
        "next_question": payload["next_question"].strip(),
    }


def _select_next_skill(session):
    skills = list(
        session.analysis.analysis_skills.select_related("skill").order_by("rank")[:8]
    )
    if not skills:
        return session.current_skill
    completed_count = session.insights.count()
    return skills[(completed_count + 1) % len(skills)].skill


def _mark_answer_error(answer, error):
    metadata = dict(answer.metadata)
    metadata.update(
        {
            "evaluation_status": "error",
            "evaluation_error": str(error)[:300],
        }
    )
    InterviewMessage.objects.filter(pk=answer.pk).update(metadata=metadata)


def _index_insight(insight, embedding_service):
    collection = ensure_collection(
        owner=insight.user,
        slug="user-analytics",
        title="Моя аналитика собеседований",
        kind=KnowledgeCollection.Kind.USER_ANALYTICS,
        embedding_service=embedding_service,
    )
    content = (
        f"Навык: {insight.skill.canonical_name if insight.skill else 'не указан'}.\n"
        f"Структурированный вывод: {insight.summary}\n"
        f"Пробелы: {', '.join(insight.gaps) or 'не указаны'}.\n"
        f"Рекомендации: {', '.join(insight.recommendations) or 'не указаны'}."
    )
    index_imported_document(
        collection=collection,
        title=f"Вывод по собеседованию #{insight.session_id}",
        content=content,
        source_type=KnowledgeDocument.SourceType.USER_ANALYTICS,
        external_id=f"insight:{insight.pk}",
        metadata={
            "session_id": insight.session_id,
            "insight_id": insight.pk,
            "question_id": insight.question_id,
            "answer_id": insight.answer_id,
        },
        skill=insight.skill,
        embedding_service=embedding_service,
    )


def submit_interview_answer(
    session,
    *,
    user,
    content=None,
    retry_answer=None,
    llm_client=None,
    retriever=None,
    embedding_service=None,
):
    if session.user_id != user.id:
        raise InterviewStateError("Собеседование недоступно")
    if session.status != InterviewSession.Status.ACTIVE:
        raise InterviewStateError("Собеседование уже завершено")

    if retry_answer is None:
        content = str(content or "").strip()
        if not content:
            raise InterviewStateError("Введите ответ")
        if len(content) > 5000:
            raise InterviewStateError("Ответ не должен превышать 5000 символов")

        with transaction.atomic():
            locked = InterviewSession.objects.select_for_update().get(pk=session.pk)
            question = locked.messages.order_by("-sequence").first()
            if question is None or question.role != InterviewMessage.Role.ASSISTANT:
                raise InterviewStateError(
                    "Предыдущий ответ ожидает повторной обработки"
                )
            answer = InterviewMessage.objects.create(
                session=locked,
                role=InterviewMessage.Role.USER,
                content=content,
                skill=question.skill,
                sequence=_next_sequence(locked),
                metadata={"evaluation_status": "pending"},
            )
    else:
        answer = retry_answer
        if answer.session_id != session.id or answer.role != InterviewMessage.Role.USER:
            raise InterviewStateError("Ответ недоступен")
        if hasattr(answer, "answer_insight"):
            raise InterviewStateError("Ответ уже обработан")
        question = (
            session.messages.filter(
                role=InterviewMessage.Role.ASSISTANT,
                sequence__lt=answer.sequence,
            )
            .order_by("-sequence")
            .first()
        )
        if question is None:
            raise InterviewStateError("Не найден вопрос для оценки")

    retriever = retriever or KnowledgeRetriever(
        embedding_service=embedding_service,
    )
    question_text = question.metadata.get("question", question.content)
    contexts = _interview_contexts(
        session,
        f"{answer.skill.canonical_name if answer.skill else ''} {question_text}",
        retriever,
    )
    system_prompt, prompt_messages = evaluation_prompt(
        question_text,
        answer.content,
        answer.skill,
        contexts,
    )
    try:
        response = (llm_client or get_llm_client()).complete(
            system_prompt,
            prompt_messages,
        )
        evaluation = _parse_evaluation(response.text)
    except CandidateTrainerError as error:
        _mark_answer_error(answer, error)
        raise

    with transaction.atomic():
        answer = InterviewMessage.objects.select_for_update().get(pk=answer.pk)
        if hasattr(answer, "answer_insight"):
            return answer.answer_insight
        locked = InterviewSession.objects.select_for_update().get(pk=session.pk)
        next_skill = _select_next_skill(locked)
        insight = InterviewInsight.objects.create(
            session=locked,
            user=user,
            skill=answer.skill,
            question=question,
            answer=answer,
            correctness=evaluation["correctness"],
            depth=evaluation["depth"],
            practical_application=evaluation["practical_application"],
            gaps=evaluation["gaps"],
            recommendations=evaluation["recommendations"],
            summary=evaluation["summary"],
            llm_provider=response.provider,
            llm_model=response.model,
        )
        metadata = dict(answer.metadata)
        metadata.update({"evaluation_status": "completed"})
        answer.metadata = metadata
        answer.save(update_fields=["metadata"])
        InterviewMessage.objects.create(
            session=locked,
            role=InterviewMessage.Role.ASSISTANT,
            content=(
                f"{evaluation['feedback']}\n\n"
                f"Следующий вопрос: {evaluation['next_question']}"
            ),
            skill=next_skill,
            sequence=_next_sequence(locked),
            metadata={
                "question": evaluation["next_question"],
                "llm_provider": response.provider,
                "llm_model": response.model,
            },
        )
        locked.current_skill = next_skill
        locked.save(update_fields=["current_skill", "updated_at"])

    try:
        _index_insight(
            insight,
            embedding_service or get_embedding_service(),
        )
    except CandidateTrainerError:
        metadata = dict(answer.metadata)
        metadata["analytics_index_status"] = "error"
        InterviewMessage.objects.filter(pk=answer.pk).update(metadata=metadata)
    return insight


def complete_interview(session, *, user):
    if session.user_id != user.id:
        raise InterviewStateError("Собеседование недоступно")
    if session.status == InterviewSession.Status.COMPLETED:
        return session
    session.status = InterviewSession.Status.COMPLETED
    session.completed_at = timezone.now()
    session.save(update_fields=["status", "completed_at", "updated_at"])
    return session
