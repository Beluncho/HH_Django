from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from .forms import KnowledgeImportForm
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
from .services.exceptions import CandidateTrainerError
from .services.knowledge_import import import_document


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
    list_display = (
        "title",
        "kind",
        "owner",
        "enabled",
        "embedding_model",
        "documents_total",
    )
    list_filter = ("kind", "enabled")
    # Включение и выключение retrieval — рутинная операция, незачем открывать
    # карточку ради одного переключателя.
    list_editable = ("enabled",)
    # Модель и размерность определяют, какими векторами наполнена коллекция.
    # Правка руками обошла бы защиту от смешивания разных моделей.
    readonly_fields = ("slug", "embedding_model", "embedding_dimension")
    search_fields = ("title", "slug")

    @admin.display(description="Документов")
    def documents_total(self, obj):
        return obj.documents.count()

    def get_urls(self):
        return [
            path(
                "import/",
                self.admin_site.admin_view(self.import_document),
                name="candidate_trainer_knowledge_import",
            ),
        ] + super().get_urls()

    def import_document(self, request):
        """Загрузка документа в базу знаний из браузера.

        Индексация синхронная: первый вызов загружает embedding-модель, дальше
        каждый фрагмент считается на CPU. Предупреждение об этом — в шаблоне.
        """
        if not self.has_add_permission(request):
            raise PermissionDenied

        form = KnowledgeImportForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            try:
                document = import_document(
                    collection_slug=form.cleaned_data["collection"],
                    raw_bytes=form.cleaned_data["file"].read(),
                    filename=form.cleaned_data["file"].name,
                    title=form.cleaned_data["title"],
                    source_type=form.cleaned_data["source_type"],
                    source_url=form.cleaned_data["source_url"],
                    normalized_skill=form.cleaned_data["skill"],
                )
            except CandidateTrainerError as error:
                # Несовпадение embedding-модели коллекции — не 500, а ошибка
                # формы: это обычная ситуация после смены модели.
                form.add_error(None, str(error))
            else:
                self.message_user(
                    request,
                    f"Документ «{document.title}» проиндексирован, "
                    f"фрагментов: {document.chunks.count()}.",
                    messages.SUCCESS,
                )
                return HttpResponseRedirect(
                    reverse(
                        "admin:candidate_trainer_knowledgecollection_changelist"
                    )
                )

        context = {
            **self.admin_site.each_context(request),
            "title": "Загрузить документ в базу знаний",
            "form": form,
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/candidate_trainer/knowledge_import.html",
            context,
        )


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "collection",
        "source_type",
        "external_id",
        "updated_at",
    )
    list_filter = ("source_type", "collection")
    search_fields = ("title", "external_id")

    def has_add_permission(self, request):
        # Документ, созданный руками, остаётся без фрагментов и молча не
        # находится при поиске. Для загрузки есть отдельная страница.
        return False


@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    """Фрагменты — производные данные от содержимого документа.

    Правка текста без пересчёта вектора разводит фрагмент и его embedding, и
    retrieval начинает находить не то, что в нём написано, — молча. Поэтому
    здесь всё только для чтения.
    """

    list_display = ("document", "chunk_index", "skill", "embedding_model")
    list_filter = ("embedding_model",)
    search_fields = ("content", "document__title")
    readonly_fields = (
        "document",
        "skill",
        "chunk_index",
        "content",
        "content_hash",
        "embedding",
        "embedding_model",
        "embedding_dimension",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):
        return False


admin.site.register(AnalysisSkill)
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
