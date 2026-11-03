from django.urls import path

from . import views

app_name = "candidate_trainer"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("analyses/<int:pk>/", views.analysis_detail, name="analysis_detail"),
    path("analyses/<int:pk>/run/", views.rerun_analysis, name="analysis_run"),
    path(
        "skills/<int:pk>/explain/",
        views.skill_explanation,
        name="skill_explanation",
    ),
    path(
        "analyses/<int:pk>/interview/",
        views.interview_create,
        name="interview_create",
    ),
    path(
        "interviews/<int:pk>/",
        views.interview_detail,
        name="interview_detail",
    ),
    path(
        "interviews/<int:pk>/answer/",
        views.interview_answer,
        name="interview_answer",
    ),
    path(
        "interviews/<int:pk>/answers/<int:answer_pk>/retry/",
        views.interview_retry,
        name="interview_retry",
    ),
    path(
        "interviews/<int:pk>/complete/",
        views.interview_complete,
        name="interview_complete",
    ),
]
