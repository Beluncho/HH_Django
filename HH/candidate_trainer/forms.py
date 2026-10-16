from django import forms
from django.conf import settings

from .models import KnowledgeDocument
from .services.analysis import normalize_query
from .services.exceptions import AnalysisValidationError
from .services.knowledge import GLOBAL_COLLECTIONS
from .services.normalization import normalize_skill


class AnalysisForm(forms.Form):
    query = forms.CharField(
        label="Название вакансии",
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Например, Python backend developer",
                "autocomplete": "off",
            }
        ),
    )
    area_id = forms.ChoiceField(
        label="Регион",
        choices=settings.HH_AREA_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean_query(self):
        try:
            query, _ = normalize_query(self.cleaned_data["query"])
        except AnalysisValidationError as error:
            raise forms.ValidationError(str(error)) from error
        return query

    @property
    def area_name(self):
        return dict(self.fields["area_id"].choices)[self.cleaned_data["area_id"]]


class InterviewAnswerForm(forms.Form):
    answer = forms.CharField(
        label="Ваш ответ",
        max_length=5000,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Сформулируйте ответ и приведите пример...",
            }
        ),
    )


class KnowledgeImportForm(forms.Form):
    """Загрузка документа в базу знаний из админки.

    Повторяет возможности команды ``import_knowledge`` за вычетом внешнего
    идентификатора: он нужен для устойчивой связи с внешним источником, а у
    загруженного руками файла такого источника нет.

    Оригинал файла не сохраняется — в базе остаются только фрагменты и имя
    файла в метаданных.
    """

    collection = forms.ChoiceField(
        label="Коллекция",
        choices=[
            (slug, config["title"])
            for slug, config in GLOBAL_COLLECTIONS.items()
        ],
        initial="interview",
    )
    file = forms.FileField(
        label="Файл",
        help_text="Только .txt, .md или .json в кодировке UTF-8.",
    )
    title = forms.CharField(
        label="Название",
        max_length=300,
        required=False,
        help_text="По умолчанию — имя файла без расширения.",
    )
    source_type = forms.ChoiceField(
        label="Тип источника",
        choices=(
            (KnowledgeDocument.SourceType.IMPORTED, "Импортированный документ"),
            (KnowledgeDocument.SourceType.VERIFIED, "Проверенный материал"),
            (KnowledgeDocument.SourceType.GENERATED, "Сгенерированный материал"),
            (KnowledgeDocument.SourceType.INTERVIEW, "Материал для интервью"),
        ),
        initial=KnowledgeDocument.SourceType.IMPORTED,
        help_text=(
            "Сгенерированный моделью текст маркируйте отдельно — выдавать его "
            "за проверенный внешний источник нельзя."
        ),
    )
    source_url = forms.URLField(label="URL источника", required=False)
    skill = forms.CharField(
        label="Навык",
        max_length=120,
        required=False,
        help_text=(
            "Необязательно. Привязывает документ к навыку: такие фрагменты "
            "видны в объяснениях этого навыка."
        ),
    )

    def clean_skill(self):
        value = (self.cleaned_data.get("skill") or "").strip()
        if not value:
            return None
        normalized = normalize_skill(value)
        if normalized is None:
            raise forms.ValidationError(
                "Не удалось распознать название навыка"
            )
        return normalized
