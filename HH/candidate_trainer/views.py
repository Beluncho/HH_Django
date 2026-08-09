from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import AnalysisForm, InterviewAnswerForm
from .models import (
    AnalysisSkill,
    InterviewInsight,
    InterviewMessage,
    InterviewSession,
    SkillExplanation,
    VacancyAnalysis,
)
from .services import (
    create_or_get_analysis,
    explain_skill,
    run_analysis,
    start_interview,
    submit_interview_answer,
)
from .services.exceptions import CandidateTrainerError
from .services.interview import complete_interview, ensure_initial_question


@login_required
def dashboard(request):
    if request.method == "POST":
        form = AnalysisForm(request.POST)
        if form.is_valid():
            analysis, created = create_or_get_analysis(
                user=request.user,
                query=form.cleaned_data["query"],
                area_id=form.cleaned_data["area_id"],
                area_name=form.area_name,
            )
            if analysis.status != VacancyAnalysis.Status.COMPLETED:
                try:
                    run_analysis(analysis.pk)
                    messages.success(request, "Анализ вакансий завершён.")
                except CandidateTrainerError as error:
                    messages.error(request, str(error))
            elif not created:
                messages.info(
                    request,
                    "Использован ранее выполненный анализ этого запроса и региона.",
                )
            return redirect("candidate_trainer:analysis_detail", pk=analysis.pk)
    elif request.method == "GET":
        form = AnalysisForm()
    else:
        return HttpResponseNotAllowed(["GET", "POST"])

    analyses = request.user.vacancy_analyses.all()[:20]
    sessions = (
        request.user.interview_sessions.select_related("analysis")
        .filter(status=InterviewSession.Status.ACTIVE)[:10]
    )
    return render(
        request,
        "candidate_trainer/dashboard.html",
        {
            "form": form,
            "analyses": analyses,
            "sessions": sessions,
        },
    )


@login_required
def analysis_detail(request, pk):
    analysis = get_object_or_404(
        VacancyAnalysis.objects.prefetch_related(
            "vacancies",
            Prefetch(
                "analysis_skills",
                queryset=AnalysisSkill.objects.select_related("skill"),
            ),
        ),
        pk=pk,
        user=request.user,
    )
    analysis_skills = list(analysis.analysis_skills.all())
    explanation_map = {}
    explanations = (
        SkillExplanation.objects.filter(
            user=request.user,
            analysis_skill__analysis=analysis,
        )
        .select_related("analysis_skill__skill")
        .order_by("analysis_skill_id", "-created_at")
    )
    for explanation in explanations:
        explanation_map.setdefault(explanation.analysis_skill_id, explanation)
    for analysis_skill in analysis_skills:
        analysis_skill.latest_explanation = explanation_map.get(analysis_skill.pk)

    return render(
        request,
        "candidate_trainer/analysis_detail.html",
        {
            "analysis": analysis,
            "analysis_skills": analysis_skills,
        },
    )


@require_POST
@login_required
def rerun_analysis(request, pk):
    analysis = get_object_or_404(VacancyAnalysis, pk=pk, user=request.user)
    if analysis.status == VacancyAnalysis.Status.RUNNING:
        messages.info(request, "Анализ уже выполняется.")
    else:
        try:
            run_analysis(analysis.pk, force=True)
            messages.success(request, "Анализ вакансий завершён.")
        except CandidateTrainerError as error:
            messages.error(request, str(error))
    return redirect("candidate_trainer:analysis_detail", pk=analysis.pk)


@require_POST
@login_required
def skill_explanation(request, pk):
    analysis_skill = get_object_or_404(
        AnalysisSkill.objects.select_related("analysis", "skill"),
        pk=pk,
        analysis__user=request.user,
    )
    try:
        explanation = explain_skill(analysis_skill, user=request.user)
        messages.success(
            request,
            f"Объяснение навыка «{analysis_skill.skill.canonical_name}» готово.",
        )
        fragment = f"#explanation-{explanation.pk}"
    except CandidateTrainerError as error:
        messages.error(request, str(error))
        fragment = ""
    detail_url = reverse(
        "candidate_trainer:analysis_detail",
        kwargs={"pk": analysis_skill.analysis_id},
    )
    return redirect(f"{detail_url}{fragment}")


@require_POST
@login_required
def interview_create(request, pk):
    analysis = get_object_or_404(VacancyAnalysis, pk=pk, user=request.user)
    try:
        session = start_interview(analysis=analysis, user=request.user)
    except CandidateTrainerError as error:
        messages.error(request, str(error))
        return redirect("candidate_trainer:analysis_detail", pk=analysis.pk)
    return redirect("candidate_trainer:interview_detail", pk=session.pk)


@login_required
def interview_detail(request, pk):
    session = get_object_or_404(
        InterviewSession.objects.select_related(
            "analysis",
            "current_skill",
        ),
        pk=pk,
        user=request.user,
    )
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    if not session.messages.exists() and session.status == InterviewSession.Status.ACTIVE:
        try:
            ensure_initial_question(session, user=request.user)
        except CandidateTrainerError as error:
            messages.error(request, str(error))

    interview_messages = list(
        session.messages.select_related("skill").order_by("sequence")
    )
    pending_answer = None
    if (
        interview_messages
        and interview_messages[-1].role == InterviewMessage.Role.USER
        and not InterviewInsight.objects.filter(
            answer=interview_messages[-1]
        ).exists()
    ):
        pending_answer = interview_messages[-1]

    return render(
        request,
        "candidate_trainer/interview.html",
        {
            "session": session,
            "interview_messages": interview_messages,
            "insights": session.insights.select_related("skill").all(),
            "pending_answer": pending_answer,
            "answer_form": InterviewAnswerForm(),
        },
    )


@require_POST
@login_required
def interview_answer(request, pk):
    session = get_object_or_404(InterviewSession, pk=pk, user=request.user)
    form = InterviewAnswerForm(request.POST)
    if form.is_valid():
        try:
            submit_interview_answer(
                session,
                user=request.user,
                content=form.cleaned_data["answer"],
            )
            messages.success(request, "Ответ сохранён и разобран.")
        except CandidateTrainerError as error:
            messages.error(request, str(error))
    else:
        messages.error(request, "Проверьте текст ответа.")
    return redirect("candidate_trainer:interview_detail", pk=session.pk)


@require_POST
@login_required
def interview_retry(request, pk, answer_pk):
    session = get_object_or_404(InterviewSession, pk=pk, user=request.user)
    answer = get_object_or_404(
        InterviewMessage,
        pk=answer_pk,
        session=session,
        role=InterviewMessage.Role.USER,
    )
    try:
        submit_interview_answer(
            session,
            user=request.user,
            retry_answer=answer,
        )
        messages.success(request, "Ответ обработан.")
    except CandidateTrainerError as error:
        messages.error(request, str(error))
    return redirect("candidate_trainer:interview_detail", pk=session.pk)


@require_POST
@login_required
def interview_complete(request, pk):
    session = get_object_or_404(InterviewSession, pk=pk, user=request.user)
    try:
        complete_interview(session, user=request.user)
        messages.success(request, "Собеседование завершено.")
    except CandidateTrainerError as error:
        messages.error(request, str(error))
    return redirect("candidate_trainer:interview_detail", pk=session.pk)
