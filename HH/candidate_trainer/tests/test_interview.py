from django.test import TestCase

from candidate_trainer.models import (
    AnalysisSkill,
    InterviewInsight,
    InterviewMessage,
    KnowledgeCollection,
    KnowledgeDocument,
    Skill,
    VacancyAnalysis,
)
from candidate_trainer.services.embeddings import HashEmbeddingService
from candidate_trainer.services.exceptions import (
    LLMError,
    RAGContextUnavailableError,
)
from candidate_trainer.services.interview import (
    ensure_initial_question,
    explain_skill,
    start_interview,
    submit_interview_answer,
)
from candidate_trainer.services.knowledge import (
    KnowledgeRetriever,
    ensure_collection,
    index_imported_document,
)
from userapp.models import WebSiteUser

from .fakes import FailingLLMClient, FailingRetriever, QueueLLMClient


class InterviewServiceTest(TestCase):
    def setUp(self):
        self.user = WebSiteUser.objects.create_user(
            username="candidate",
            email="candidate@example.com",
            password="test-password",
        )
        self.analysis = VacancyAnalysis.objects.create(
            user=self.user,
            query="Python developer",
            normalized_query="python developer",
            area_id="1",
            area_name="Москва",
            cache_key="cache",
            status=VacancyAnalysis.Status.COMPLETED,
            vacancies_processed=2,
        )
        self.skill = Skill.objects.create(
            canonical_name="Python",
            normalized_name="python",
        )
        self.analysis_skill = AnalysisSkill.objects.create(
            analysis=self.analysis,
            skill=self.skill,
            vacancy_count=2,
            frequency_percent="100.00",
            rank=1,
            variants=["Python"],
        )
        self.embedding_service = HashEmbeddingService(
            dimension=16,
            model_name="test-hash-v1",
        )

    def create_question(self, session):
        return InterviewMessage.objects.create(
            session=session,
            role=InterviewMessage.Role.ASSISTANT,
            content="Что такое контекстный менеджер?",
            skill=self.skill,
            sequence=1,
            metadata={"question": "Что такое контекстный менеджер?"},
        )

    def evaluation(self):
        return {
            "correctness": 4,
            "depth": 3,
            "practical_application": 4,
            "gaps": ["Не упомянут протокол __exit__"],
            "recommendations": ["Повторить contextlib"],
            "summary": "Ответ в основном корректен.",
            "feedback": "Хорошая основа, но уточните протокол.",
            "next_question": "Как работает декоратор contextmanager?",
        }

    def test_interview_works_when_rag_is_disabled(self):
        session = start_interview(analysis=self.analysis, user=self.user)
        session.interview_rag_enabled = False
        session.save(update_fields=["interview_rag_enabled"])
        llm = QueueLLMClient(["Что такое GIL?"])

        message = ensure_initial_question(
            session,
            user=self.user,
            llm_client=llm,
            retriever=FailingRetriever(),
        )

        self.assertEqual(message.content, "Что такое GIL?")
        self.assertEqual(session.messages.count(), 1)

    def test_interview_falls_back_when_collection_is_empty(self):
        ensure_collection(
            slug="interview",
            title="Интервью",
            kind=KnowledgeCollection.Kind.INTERVIEW,
            embedding_service=self.embedding_service,
        )
        session = start_interview(analysis=self.analysis, user=self.user)

        message = ensure_initial_question(
            session,
            user=self.user,
            llm_client=QueueLLMClient(["Вопрос без RAG"]),
            retriever=FailingRetriever(),
        )

        self.assertEqual(message.content, "Вопрос без RAG")

    def test_successful_answer_creates_messages_insight_and_private_analytics(self):
        session = start_interview(analysis=self.analysis, user=self.user)
        self.create_question(session)
        raw_answer = "RAW_PRIVATE_ANSWER используется with-блок."

        insight = submit_interview_answer(
            session,
            user=self.user,
            content=raw_answer,
            llm_client=QueueLLMClient([self.evaluation()]),
            embedding_service=self.embedding_service,
        )

        self.assertEqual(session.messages.count(), 3)
        self.assertEqual(InterviewInsight.objects.count(), 1)
        self.assertEqual(insight.answer.content, raw_answer)
        collection = KnowledgeCollection.objects.get(
            owner=self.user,
            kind=KnowledgeCollection.Kind.USER_ANALYTICS,
        )
        indexed_content = collection.documents.get().chunks.get().content
        self.assertNotIn("RAW_PRIVATE_ANSWER", indexed_content)
        self.assertEqual(insight.question.content, "Что такое контекстный менеджер?")

    def test_llm_error_keeps_answer_without_partial_insight(self):
        session = start_interview(analysis=self.analysis, user=self.user)
        self.create_question(session)

        with self.assertRaises(LLMError):
            submit_interview_answer(
                session,
                user=self.user,
                content="Сохранённый ответ",
                llm_client=FailingLLMClient(),
                embedding_service=self.embedding_service,
            )

        self.assertEqual(session.messages.count(), 2)
        self.assertEqual(session.insights.count(), 0)
        answer = session.messages.get(role=InterviewMessage.Role.USER)
        self.assertEqual(answer.content, "Сохранённый ответ")
        self.assertEqual(answer.metadata["evaluation_status"], "error")

    def test_failed_answer_can_be_retried_without_duplicate_user_message(self):
        session = start_interview(analysis=self.analysis, user=self.user)
        self.create_question(session)
        with self.assertRaises(LLMError):
            submit_interview_answer(
                session,
                user=self.user,
                content="Ответ",
                llm_client=FailingLLMClient(),
                embedding_service=self.embedding_service,
            )
        answer = session.messages.get(role=InterviewMessage.Role.USER)

        submit_interview_answer(
            session,
            user=self.user,
            retry_answer=answer,
            llm_client=QueueLLMClient([self.evaluation()]),
            embedding_service=self.embedding_service,
        )

        self.assertEqual(
            session.messages.filter(role=InterviewMessage.Role.USER).count(),
            1,
        )
        self.assertEqual(session.insights.count(), 1)

    def test_explanation_requires_nonempty_skill_core(self):
        ensure_collection(
            slug="skill-core",
            title="Навыки",
            kind=KnowledgeCollection.Kind.SKILL_CORE,
            embedding_service=self.embedding_service,
        )

        with self.assertRaises(RAGContextUnavailableError):
            explain_skill(
                self.analysis_skill,
                user=self.user,
                llm_client=QueueLLMClient(["Текст"]),
                retriever=KnowledgeRetriever(self.embedding_service),
            )

    def test_explanation_uses_filled_skill_core(self):
        collection = ensure_collection(
            slug="skill-core",
            title="Навыки",
            kind=KnowledgeCollection.Kind.SKILL_CORE,
            embedding_service=self.embedding_service,
        )
        index_imported_document(
            collection=collection,
            title="Python guide",
            content="Контекстный менеджер освобождает ресурсы после with-блока.",
            source_type=KnowledgeDocument.SourceType.VERIFIED,
            source_url="https://docs.example/python",
            skill=self.skill,
            embedding_service=self.embedding_service,
        )

        explanation = explain_skill(
            self.analysis_skill,
            user=self.user,
            llm_client=QueueLLMClient(["Объяснение навыка"]),
            retriever=KnowledgeRetriever(self.embedding_service),
        )

        self.assertEqual(explanation.content, "Объяснение навыка")
        self.assertEqual(explanation.sources[0]["source_type"], "verified")
