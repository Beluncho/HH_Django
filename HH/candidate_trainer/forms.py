from django import forms
from django.conf import settings

from .services.analysis import normalize_query
from .services.exceptions import AnalysisValidationError


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
