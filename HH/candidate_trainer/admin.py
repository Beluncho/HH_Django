from django.contrib import admin

from .models import (
    AnalysisSkill,
    HHVacancySnapshot,
    InterviewInsight,
    InterviewMessage,
    InterviewSession,
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeDocument,
    LLMRequestLog,
    Skill,
    SkillExplanation,
    VacancyAnalysis,
)


@admin.register(VacancyAnalysis)
class VacancyAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "query",
        "area_name",
        "user",
        "status",
        "vacancies_processed",
        "created_at",
    )
    list_filter = ("status", "area_name")
    search_fields = ("query", "user__username")


@admin.register(HHVacancySnapshot)
class HHVacancySnapshotAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "external_id", "published_at")
    search_fields = ("title", "employer", "external_id")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("canonical_name", "embedding_model", "updated_at")
    search_fields = ("canonical_name", "normalized_name")


@admin.register(KnowledgeCollection)
class KnowledgeCollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "owner", "enabled", "embedding_model")
    list_filter = ("kind", "enabled")


admin.site.register(AnalysisSkill)
admin.site.register(KnowledgeDocument)
admin.site.register(KnowledgeChunk)
admin.site.register(SkillExplanation)
admin.site.register(InterviewSession)
admin.site.register(InterviewMessage)
admin.site.register(InterviewInsight)


@admin.register(LLMRequestLog)
class LLMRequestLogAdmin(admin.ModelAdmin):
    """Журнал обращений к LLM — только для чтения.

    Это следы работы системы, а не данные: записи создаёт код, а руками их
    править нечего. Текстов промтов и ответов здесь нет (см. модель).
    """

    list_display = (
        "created_at",
        "operation",
        "status",
        "provider",
        "model",
        "duration_ms",
        "http_status",
        "user",
    )
    list_filter = ("status", "operation", "provider")
    search_fields = ("error_detail", "model", "user__username")
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at",
        "operation",
        "status",
        "provider",
        "model",
        "duration_ms",
        "http_status",
        "error_detail",
        "prompt_tokens",
        "completion_tokens",
        "user",
    )

    def has_add_permission(self, request):
        return False
