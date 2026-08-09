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
