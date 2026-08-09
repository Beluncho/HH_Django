from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class VacancyAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает запуска"
        RUNNING = "running", "Выполняется"
        COMPLETED = "completed", "Завершён"
        FAILED = "failed", "Ошибка"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vacancy_analyses",
    )
    query = models.CharField(max_length=200)
    normalized_query = models.CharField(max_length=200)
    area_id = models.CharField(max_length=20)
    area_name = models.CharField(max_length=120)
    cache_key = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.CharField(max_length=500, blank=True)
    vacancies_found = models.PositiveSmallIntegerField(default=0)
    vacancies_processed = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    vacancies = models.ManyToManyField(
        "HHVacancySnapshot",
        related_name="analyses",
        blank=True,
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "cache_key"),
                name="unique_candidate_analysis_cache",
            ),
        ]
        indexes = [
            models.Index(fields=("user", "status", "-created_at")),
        ]

    def __str__(self):
        return f"{self.query} — {self.area_name}"


class HHVacancySnapshot(models.Model):
    source = models.CharField(max_length=30, default="hh")
    external_id = models.CharField(max_length=50)
    title = models.CharField(max_length=300)
    employer = models.CharField(max_length=300, blank=True)
    url = models.URLField(max_length=500)
    published_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    raw_skills = models.JSONField(default=list)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source", "external_id"),
                name="unique_external_vacancy_snapshot",
            ),
        ]
        ordering = ("-published_at", "-fetched_at")

    def __str__(self):
        return self.title


class Skill(models.Model):
    canonical_name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=120, unique=True)
    embedding = models.JSONField(default=list, blank=True)
    embedding_model = models.CharField(max_length=200, blank=True)
    embedding_dimension = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("canonical_name",)

    def __str__(self):
        return self.canonical_name


class AnalysisSkill(models.Model):
    analysis = models.ForeignKey(
        VacancyAnalysis,
        on_delete=models.CASCADE,
        related_name="analysis_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="analysis_occurrences",
    )
    vacancy_count = models.PositiveSmallIntegerField()
    frequency_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    rank = models.PositiveSmallIntegerField()
    variants = models.JSONField(default=list)

    class Meta:
        ordering = ("rank", "skill__canonical_name")
        constraints = [
            models.UniqueConstraint(
                fields=("analysis", "skill"),
                name="unique_skill_per_analysis",
            ),
        ]

    def __str__(self):
        return f"{self.skill}: {self.vacancy_count}"


class KnowledgeCollection(models.Model):
    class Kind(models.TextChoices):
        SKILL_CORE = "skill_core", "Навыки"
        INTERVIEW = "interview", "Собеседование"
        USER_ANALYTICS = "user_analytics", "Аналитика пользователя"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="knowledge_collections",
        null=True,
        blank=True,
    )
    slug = models.SlugField(max_length=80)
    title = models.CharField(max_length=150)
    kind = models.CharField(max_length=30, choices=Kind.choices)
    enabled = models.BooleanField(default=True)
    embedding_model = models.CharField(max_length=200, blank=True)
    embedding_dimension = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("kind", "title")
        constraints = [
            models.UniqueConstraint(
                fields=("owner", "slug"),
                name="unique_owner_knowledge_collection",
            ),
            models.UniqueConstraint(
                fields=("slug",),
                condition=Q(owner__isnull=True),
                name="unique_global_knowledge_collection",
            ),
        ]

    def __str__(self):
        return self.title


class KnowledgeDocument(models.Model):
    class SourceType(models.TextChoices):
        HH = "hh", "HH.ru"
        IMPORTED = "imported", "Импортированный документ"
        VERIFIED = "verified", "Проверенный материал"
        GENERATED = "generated", "Сгенерированный материал"
        INTERVIEW = "interview", "Материал для интервью"
        USER_ANALYTICS = "user_analytics", "Пользовательская аналитика"

    collection = models.ForeignKey(
        KnowledgeCollection,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=300)
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    source_url = models.URLField(max_length=500, blank=True)
    external_id = models.CharField(max_length=100, blank=True)
    retrieved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=("collection", "external_id")),
        ]

    def __str__(self):
        return self.title


class KnowledgeChunk(models.Model):
    document = models.ForeignKey(
        KnowledgeDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.SET_NULL,
        related_name="knowledge_chunks",
        null=True,
        blank=True,
    )
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    content_hash = models.CharField(max_length=64)
    embedding = models.JSONField(default=list, blank=True)
    embedding_model = models.CharField(max_length=200, blank=True)
    embedding_dimension = models.PositiveSmallIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("document", "chunk_index")
        constraints = [
            models.UniqueConstraint(
                fields=("document", "chunk_index"),
                name="unique_document_chunk_index",
            ),
        ]
        indexes = [
            models.Index(fields=("skill", "embedding_model")),
        ]

    def __str__(self):
        return f"{self.document} [{self.chunk_index}]"


class SkillExplanation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_explanations",
    )
    analysis_skill = models.ForeignKey(
        AnalysisSkill,
        on_delete=models.CASCADE,
        related_name="explanations",
    )
    content = models.TextField()
    sources = models.JSONField(default=list)
    llm_provider = models.CharField(max_length=50, blank=True)
    llm_model = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class InterviewSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активно"
        COMPLETED = "completed", "Завершено"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_sessions",
    )
    analysis = models.ForeignKey(
        VacancyAnalysis,
        on_delete=models.CASCADE,
        related_name="interview_sessions",
    )
    current_skill = models.ForeignKey(
        Skill,
        on_delete=models.SET_NULL,
        related_name="current_interviews",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    interview_rag_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Собеседование #{self.pk}: {self.analysis}"


class InterviewMessage(models.Model):
    class Role(models.TextChoices):
        ASSISTANT = "assistant", "Интервьюер"
        USER = "user", "Кандидат"

    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    skill = models.ForeignKey(
        Skill,
        on_delete=models.SET_NULL,
        related_name="interview_messages",
        null=True,
        blank=True,
    )
    sequence = models.PositiveIntegerField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sequence",)
        constraints = [
            models.UniqueConstraint(
                fields=("session", "sequence"),
                name="unique_interview_message_sequence",
            ),
        ]

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:60]}"


class InterviewInsight(models.Model):
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="insights",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_insights",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.SET_NULL,
        related_name="interview_insights",
        null=True,
        blank=True,
    )
    question = models.ForeignKey(
        InterviewMessage,
        on_delete=models.PROTECT,
        related_name="question_insights",
    )
    answer = models.OneToOneField(
        InterviewMessage,
        on_delete=models.PROTECT,
        related_name="answer_insight",
    )
    correctness = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    depth = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    practical_application = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    gaps = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    summary = models.TextField()
    llm_provider = models.CharField(max_length=50, blank=True)
    llm_model = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Вывод по ответу #{self.answer_id}"
