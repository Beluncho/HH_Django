# План улучшений UX и архитектуры candidate_trainer

**Дата создания:** 23.10.2026  
**Версия:** 1.0  
**Статус:** В разработке

---

## Цели

1. Улучшить навигацию по активным собеседованиям
2. Оптимизировать хранение и переиспользование объяснений навыков
3. Улучшить UX длинных страниц через боковую навигацию

---

## Этап 1: Управление собеседованиями

### Статус: ✅ Выполнен

### Комментарий
Реализовано 2025-01-XX. Добавлены кнопки "Продолжить" для активных сессий с отображением даты и количества сообщений. Кнопка "Начать новое собеседование" сохранена.

### Проблема
- При каждом нажатии "Начать собеседование" создаётся новая сессия
- Старые активные сессии остаются в статусе ACTIVE
- На dashboard показываются все активные сессии, но нельзя продолжить
- Нет способа вернуться к незавершённому собеседованию

### Решение
Добавить возможность продолжить существующие активные сессии + оставить создание новых.

### Задачи

#### 1.1. Обновить view analysis_detail
- [x] Загружать активные сессии пользователя для текущего анализа
- [x] Передавать в контекст шаблона
- [x] Добавить аннотацию message_count через Count

**Файлы:**
- `candidate_trainer/views.py` - функция `analysis_detail`

**Изменения:**
```python
# Добавлено в context:
active_sessions = (
    analysis.interview_sessions.filter(
        user=request.user, status=InterviewSession.Status.ACTIVE
    )
    .annotate(message_count=Count("messages"))
    .order_by("-created_at")
)
```

#### 1.2. Обновить шаблон analysis_detail.html
- [x] Добавить отображение активных сессий перед кнопкой "Начать собеседование"
- [x] Показать кнопки "Продолжить" для каждой активной сессии
- [x] Показать дату создания и количество сообщений
- [x] Сохранить кнопку "Начать новое собеседование"

**Файлы:**
- `candidate_trainer/templates/candidate_trainer/analysis_detail.html`

**Структура UI:**
```html
<section class="content-section" aria-labelledby="interviews-title">
    <div class="section-heading">
        <h2 id="interviews-title">Собеседования</h2>
    </div>
    
    {% if active_sessions %}
    <div class="session-list">
        {% for session in active_sessions %}
        <div class="session-row">
            <div>
                <strong>Собеседование #{{ session.pk }}</strong>
                <small>Начато {{ session.created_at|date:"d.m.Y H:i" }} · {{ session.messages.count }} сообщений</small>
            </div>
            <a href="{% url 'candidate_trainer:interview_detail' pk=session.pk %}" 
               class="btn btn-sm btn-primary">
                <i class="bi bi-arrow-right-circle"></i>
                Продолжить
            </a>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <form method="post" action="{% url 'candidate_trainer:interview_create' pk=analysis.pk %}">
        {% csrf_token %}
        <button class="btn btn-dark" type="submit" data-busy="Готовлю первый вопрос…">
            <i class="bi bi-plus-circle"></i>
            Начать новое собеседование
        </button>
    </form>
</section>
```

#### 1.3. Опционально: Быстрое завершение сессии
- [ ] Добавить кнопку "Завершить" в списке активных сессий (без перехода)
- [ ] Создать endpoint для завершения сессии через POST

**Файлы:**
- `candidate_trainer/views.py` - новая функция `interview_quick_complete`
- `candidate_trainer/urls.py` - новый URL

### Критерии приёмки
✅ Пользователь видит все активные собеседования для анализа  
✅ Может продолжить любое из них одним кликом  
✅ Может начать новое собеседование параллельно  
✅ Видит дату и прогресс каждой сессии  

### Комментарии
_Пусто - этап не начат_

---

## Этап 2: Глобальная база объяснений навыков

### Статус: ⏳ Не начат

### Проблема
- Текущая модель: `SkillExplanation(user, analysis_skill)`
- При повторном "Объяснить" создаётся дубликат
- Объяснение изолировано для каждого пользователя
- Не переиспользуется между анализами
- Растёт количество идентичных объяснений "Python", "SQL" и т.д.

### Решение
**Вариант B: Глобальная база знаний + версионность по времени**

- Один навык = одно глобальное объяснение для всех пользователей
- При запросе пользователя проверяется давность последнего объяснения
- Если объяснение старше 1 года → создаётся новое (старое помечается `is_active=False`)
- Если свежее → возвращается существующее
- Архитектура готова к персонализации (user IS NOT NULL для будущих кастомных объяснений)

**Важно:** Обновление происходит **только по запросу пользователя**, не автоматически в фоне.

### Задачи

#### 2.1. Изменить модель SkillExplanation
- [ ] Убрать `analysis_skill` (ForeignKey к AnalysisSkill)
- [ ] Добавить `skill` (ForeignKey к Skill)
- [ ] Изменить `user` на nullable (NULL = глобальное объяснение)
- [ ] Добавить `is_active` (Boolean, default=True) для версионности
- [ ] Добавить constraint: UNIQUE(skill) WHERE user IS NULL AND is_active=True
- [ ] Добавить constraint: UNIQUE(user, skill) WHERE user IS NOT NULL AND is_active=True
- [ ] Добавить индексы: (skill, user, is_active), (skill, is_active, -created_at)

**Файлы:**
- `candidate_trainer/models.py` - класс `SkillExplanation`

**Изменения:**
```python
class SkillExplanation(models.Model):
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="explanations",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_explanations",
        null=True,  # NULL = глобальное объяснение
        blank=True,
    )
    content = models.TextField()
    sources = models.JSONField(default=list)
    llm_provider = models.CharField(max_length=50, blank=True)
    llm_model = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("skill",),
                condition=Q(user__isnull=True, is_active=True),
                name="unique_active_global_skill_explanation",
            ),
            models.UniqueConstraint(
                fields=("user", "skill"),
                condition=Q(user__isnull=False, is_active=True),
                name="unique_active_user_skill_explanation",
            ),
        ]
        indexes = [
            models.Index(fields=("skill", "user", "is_active")),
            models.Index(fields=("skill", "is_active", "-created_at")),
        ]
    
    @property
    def is_outdated(self):
        """Возвращает True, если объяснение старше 6 месяцев."""
        from datetime import timedelta
        from django.utils import timezone
        age = timezone.now() - self.created_at
        return age > timedelta(days=180)
```

#### 2.2. Создать миграцию с data migration
- [ ] Создать миграцию для изменения схемы
- [ ] Написать data migration для переноса существующих записей
- [ ] Дедупликация: для каждой пары (user, skill) оставить последнюю запись
- [ ] Для глобальных: взять skill из analysis_skill, установить user=NULL

**Файлы:**
- `candidate_trainer/migrations/00XX_update_skill_explanation.py`

**Логика data migration:**
```python
def migrate_explanations(apps, schema_editor):
    SkillExplanation = apps.get_model('candidate_trainer', 'SkillExplanation')
    
    # Для каждой существующей записи:
    # 1. Извлечь skill из analysis_skill.skill
    # 2. Установить user=NULL (делаем глобальными)
    # 3. Удалить дубликаты: для каждого skill оставить последнюю
    
    # Группировка и дедупликация
    from django.db.models import Max
    latest_per_skill = SkillExplanation.objects.values('skill').annotate(
        latest_created=Max('created_at')
    )
    
    # Оставить только последние, остальные пометить is_active=False
```

#### 2.3. Обновить сервис explain_skill
- [ ] Изменить сигнатуру: принимать `skill` вместо `analysis_skill`
- [ ] Проверять наличие глобального объяснения (user=NULL, is_active=True)
- [ ] Проверять давность: если >= 365 дней → деактивировать и создать новое
- [ ] Если < 365 дней → вернуть существующее
- [ ] Если нет → создать новое глобальное объяснение

**Файлы:**
- `candidate_trainer/services/interview.py` - функция `explain_skill`

**Логика:**
```python
from datetime import timedelta
from django.utils import timezone

def explain_skill(skill: Skill) -> SkillExplanation:
    """
    Получить или создать глобальное объяснение навыка.
    
    Логика:
    1. Проверяем наличие активного глобального объяснения
    2. Если есть и свежее года (< 365 дней) → возвращаем
    3. Если есть но устарело (>= 365 дней) → деактивируем, создаём новое
    4. Если нет → создаём новое
    
    Args:
        skill: Навык для объяснения
    
    Returns:
        SkillExplanation: Глобальное объяснение
    """
    # Ищем активное глобальное объяснение
    existing = SkillExplanation.objects.filter(
        skill=skill,
        user__isnull=True,
        is_active=True,
    ).first()
    
    if existing:
        age = timezone.now() - existing.created_at
        
        # Если свежее года — возвращаем
        if age < timedelta(days=365):
            return existing
        
        # Устарело — деактивируем
        existing.is_active = False
        existing.save(update_fields=["is_active"])
    
    # Создаём новое глобальное объяснение
    rag_context = retrieve_skill_context(skill)
    explanation_text = generate_skill_explanation(skill, rag_context)
    
    explanation = SkillExplanation.objects.create(
        skill=skill,
        user=None,  # Глобальное
        content=explanation_text,
        sources=rag_context.get("sources", []),
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL,
        is_active=True,
    )
    
    return explanation
```

#### 2.4. Обновить view skill_explanation
- [ ] Извлекать `skill` из `analysis_skill.skill`
- [ ] Передавать `skill` в сервис `explain_skill`
- [ ] Убрать передачу `user` (не нужен для глобальных объяснений)

**Файлы:**
- `candidate_trainer/views.py` - функция `skill_explanation`

**Изменения:**
```python
@require_POST
@login_required
def skill_explanation(request, pk):
    analysis_skill = get_object_or_404(
        AnalysisSkill.objects.select_related("analysis", "skill"),
        pk=pk,
        analysis__user=request.user,
    )
    
    skill = analysis_skill.skill
    
    try:
        explanation = explain_skill(skill)  # Передаём skill, а не analysis_skill
        messages.success(
            request,
            f"Объяснение навыка «{skill.canonical_name}» готово.",
        )
        fragment = f"#explanation-{explanation.pk}"
    except CandidateTrainerError as error:
        messages.error(request, humanize_llm_error(error))
        fragment = ""
    
    detail_url = reverse(
        "candidate_trainer:analysis_detail",
        kwargs={"pk": analysis_skill.analysis_id},
    )
    return redirect(f"{detail_url}{fragment}")
```

#### 2.5. Обновить view analysis_detail
- [ ] Загружать глобальные объяснения по skill_id вместо analysis_skill_id
- [ ] Маппинг: skill_id → explanation
- [ ] Прикреплять объяснение к analysis_skill для отображения

**Файлы:**
- `candidate_trainer/views.py` - функция `analysis_detail`

**Изменения:**
```python
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
    
    # Получаем skill_id для всех навыков анализа
    skill_ids = [as_.skill_id for as_ in analysis_skills]
    
    # Загружаем активные глобальные объяснения
    explanations = SkillExplanation.objects.filter(
        skill_id__in=skill_ids,
        user__isnull=True,
        is_active=True,
    ).select_related("skill")
    
    explanation_map = {exp.skill_id: exp for exp in explanations}
    
    # Прикрепляем объяснения к навыкам
    for analysis_skill in analysis_skills:
        analysis_skill.explanation = explanation_map.get(analysis_skill.skill_id)
    
    # Активные сессии для этапа 1
    active_sessions = request.user.interview_sessions.filter(
        analysis=analysis,
        status=InterviewSession.Status.ACTIVE,
    ).order_by('-created_at')[:5]
    
    return render(
        request,
        "candidate_trainer/analysis_detail.html",
        {
            "analysis": analysis,
            "analysis_skills": analysis_skills,
            "active_sessions": active_sessions,
        },
    )
```

#### 2.6. Обновить шаблон analysis_detail.html
- [ ] Изменить логику кнопок: если есть объяснение → "Посмотреть", если нет → "Объяснить"
- [ ] Добавить индикатор давности объяснения (если > 6 месяцев)
- [ ] Изменить отображение объяснений: использовать `item.explanation` вместо `item.latest_explanation`

**Файлы:**
- `candidate_trainer/templates/candidate_trainer/analysis_detail.html`

**Изменения в таблице навыков:**
```html
<td class="text-end">
    {% if item.explanation %}
        <a class="btn btn-sm btn-success" href="#explanation-{{ item.explanation.pk }}">
            <i class="bi bi-check-circle" aria-hidden="true"></i>
            Посмотреть
        </a>
    {% else %}
        <form method="post" action="{% url 'candidate_trainer:skill_explanation' pk=item.pk %}">
            {% csrf_token %}
            <button class="btn btn-sm btn-outline-primary" type="submit" data-busy="Объясняю…">
                <i class="bi bi-book" aria-hidden="true"></i>
                Объяснить
            </button>
        </form>
    {% endif %}
</td>
```

**Изменения в блоке объяснений:**
```html
{% for item in analysis_skills %}
    {% if item.explanation %}
    <section class="explanation-block" id="explanation-{{ item.explanation.pk }}">
        <div class="section-heading">
            <h2>{{ item.skill.canonical_name }}</h2>
            <span class="section-note">
                {{ item.explanation.created_at|date:"d.m.Y" }}
                {% if item.explanation.is_outdated %}
                    <span class="badge bg-warning text-dark">Обновлено более 6 месяцев назад</span>
                {% endif %}
            </span>
        </div>
        <div class="explanation-text">{{ item.explanation.content|render_markdown }}</div>
        <details>
            <summary>Источники контекста ({{ item.explanation.sources|length }})</summary>
            <ul class="source-list">
                {% for source in item.explanation.sources %}
                <li>
                    {% if source.url %}
                    <a href="{{ source.url }}" target="_blank" rel="noopener noreferrer">{{ source.title }}</a>
                    {% else %}
                    {{ source.title }}
                    {% endif %}
                    <span>{{ source.source_type }}</span>
                </li>
                {% endfor %}
            </ul>
        </details>
    </section>
    {% endif %}
{% endfor %}
```

#### 2.7. Обновить админку
- [ ] Добавить фильтры: is_active, user__isnull (глобальные/персональные)
- [ ] Показать skill, user, created_at, is_active, llm_model
- [ ] Добавить action "Деактивировать объяснения" (массовое)
- [ ] Добавить action "Обновить объяснение" (пересоздать)

**Файлы:**
- `candidate_trainer/admin.py` - класс `SkillExplanationAdmin`

**Структура:**
```python
@admin.register(SkillExplanation)
class SkillExplanationAdmin(admin.ModelAdmin):
    list_display = ("skill", "user_type", "created_at", "is_active", "llm_model", "is_outdated")
    list_filter = ("is_active", "llm_provider", "created_at", ("user", admin.EmptyFieldListFilter))
    search_fields = ("skill__canonical_name",)
    readonly_fields = ("created_at",)
    
    def user_type(self, obj):
        return "Глобальное" if obj.user is None else f"Персональное ({obj.user.username})"
    user_type.short_description = "Тип"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("skill", "user")
    
    actions = ["deactivate_explanations", "refresh_explanation"]
    
    def deactivate_explanations(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано объяснений: {count}")
    deactivate_explanations.short_description = "Деактивировать выбранные объяснения"
```

#### 2.8. Написать тесты
- [ ] Тест: создание первого глобального объяснения
- [ ] Тест: повторный запрос возвращает существующее (< 1 года)
- [ ] Тест: запрос с устаревшим объяснением создаёт новое и деактивирует старое
- [ ] Тест: is_outdated property работает корректно
- [ ] Тест: constraints работают (нельзя создать дубликат глобального активного)
- [ ] Тест: UI показывает "Посмотреть" когда объяснение есть

**Файлы:**
- `candidate_trainer/tests/test_skill_explanation.py` (новый файл)

### Критерии приёмки
✅ Один навык имеет одно глобальное объяснение для всех пользователей  
✅ При запросе проверяется давность: если >= 1 года → создаётся новое  
✅ Старые версии сохраняются с is_active=False для истории  
✅ Экономия LLM-запросов: объяснение создаётся один раз и переиспользуется  
✅ В UI видно, есть ли объяснение (кнопка "Посмотреть" vs "Объяснить")  
✅ Показывается индикатор устаревшего объяснения (> 6 месяцев)  
✅ Архитектура готова к персонализации через user IS NOT NULL  

### Комментарии
_Пусто - этап не начат_

---

## Этап 3: Улучшение навигации (Sticky Sidebar)

### Статус: ⏳ Не начат

### Проблема
- Страница analysis_detail может быть очень длинной:
  - Таблица навыков
  - Секция собеседований (после этапа 1)
  - Блоки объяснений (может быть 20+ навыков)
  - Список вакансий (20 карточек)
- Приходится много скроллить колёсиком мыши
- Нет быстрого способа перейти к нужному разделу

### Решение
**Sticky sidebar с якорной навигацией + схлопываемые объяснения**

- Боковая панель с навигацией по разделам (sticky position)
- Автоподсветка активного раздела при скролле
- Схлопываемые блоки объяснений (details/summary)
- Responsive: на мобилке sidebar скрывается, появляется кнопка меню

### Задачи

#### 3.1. Обновить HTML структуру analysis_detail.html
- [ ] Обернуть контент в layout с sidebar
- [ ] Добавить aside.analysis-sidebar с навигацией
- [ ] Добавить ID для каждой секции (skills, explanations, interviews, vacancies)
- [ ] Добавить счётчики элементов в навигацию

**Файлы:**
- `candidate_trainer/templates/candidate_trainer/analysis_detail.html`

**Структура:**
```html
<div class="analysis-layout">
    <!-- Sidebar navigation -->
    <aside class="analysis-sidebar">
        <nav class="sidebar-nav" aria-label="Навигация по разделам">
            <a href="#skills" class="sidebar-link">
                <i class="bi bi-list-check"></i>
                Навыки
                <span class="badge">{{ analysis_skills|length }}</span>
            </a>
            <a href="#explanations" class="sidebar-link">
                <i class="bi bi-book"></i>
                Объяснения
                <span class="badge">{{ explanations_count }}</span>
            </a>
            <a href="#interviews" class="sidebar-link">
                <i class="bi bi-chat-square-text"></i>
                Собеседования
                <span class="badge">{{ active_sessions|length }}</span>
            </a>
            <a href="#vacancies" class="sidebar-link">
                <i class="bi bi-briefcase"></i>
                Вакансии
                <span class="badge">{{ analysis.vacancies_processed }}</span>
            </a>
        </nav>
    </aside>
    
    <!-- Main content -->
    <main class="analysis-content">
        <section id="skills" class="content-section">
            <!-- Таблица навыков -->
        </section>
        
        <section id="explanations" class="content-section">
            <!-- Объяснения (схлопываемые) -->
        </section>
        
        <section id="interviews" class="content-section">
            <!-- Список собеседований -->
        </section>
        
        <section id="vacancies" class="content-section">
            <!-- Список вакансий -->
        </section>
    </main>
</div>
```

#### 3.2. Сделать объяснения схлопываемыми
- [ ] Обернуть каждое объяснение в <details>
- [ ] Добавить превью первых 150 символов в <summary>
- [ ] Открывать автоматически, если есть якорь #explanation-{id}

**Изменения в блоке объяснений:**
```html
<section id="explanations" class="content-section">
    <h2>Объяснения навыков</h2>
    {% for item in analysis_skills %}
        {% if item.explanation %}
        <details class="explanation-details" id="explanation-{{ item.explanation.pk }}">
            <summary class="explanation-summary">
                <strong>{{ item.skill.canonical_name }}</strong>
                <span class="explanation-preview">{{ item.explanation.content|striptags|truncatewords:20 }}</span>
                <span class="explanation-date">{{ item.explanation.created_at|date:"d.m.Y" }}</span>
            </summary>
            <div class="explanation-content">
                <div class="explanation-text">{{ item.explanation.content|render_markdown }}</div>
                <details>
                    <summary>Источники контекста</summary>
                    <!-- ... -->
                </details>
            </div>
        </details>
        {% endif %}
    {% endfor %}
</section>
```

#### 3.3. Добавить CSS для sidebar
- [ ] Sticky position для sidebar
- [ ] Подсветка активного пункта
- [ ] Анимация hover/active состояний
- [ ] Responsive: скрыть sidebar на экранах < 900px
- [ ] Стили для схлопываемых объяснений

**Файлы:**
- `candidate_trainer/static/candidate_trainer/css/trainer.css`

**CSS:**
```css
/* Analysis layout with sidebar */
.analysis-layout {
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 32px;
    align-items: start;
}

.analysis-sidebar {
    position: sticky;
    top: 88px; /* header height + padding */
    max-height: calc(100vh - 112px);
    overflow-y: auto;
}

.sidebar-nav {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.sidebar-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 6px;
    color: var(--ink);
    text-decoration: none;
    transition: background 0.2s;
}

.sidebar-link:hover {
    background: var(--canvas);
    color: var(--primary);
}

.sidebar-link.active {
    background: var(--primary);
    color: white;
}

.sidebar-link .badge {
    margin-left: auto;
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 10px;
    background: var(--line);
}

.sidebar-link.active .badge {
    background: rgba(255, 255, 255, 0.3);
}

.analysis-content {
    min-width: 0; /* Prevent grid overflow */
}

/* Collapsible explanations */
.explanation-details {
    border: 1px solid var(--line);
    border-radius: 6px;
    margin-bottom: 12px;
    background: var(--surface);
}

.explanation-summary {
    padding: 16px 18px;
    cursor: pointer;
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 12px;
    align-items: center;
    list-style: none; /* Remove default arrow */
}

.explanation-summary::-webkit-details-marker {
    display: none;
}

.explanation-summary::before {
    content: "▶";
    color: var(--muted);
    transition: transform 0.2s;
}

.explanation-details[open] .explanation-summary::before {
    transform: rotate(90deg);
}

.explanation-preview {
    color: var(--muted);
    font-size: 14px;
}

.explanation-date {
    color: var(--muted);
    font-size: 12px;
    white-space: nowrap;
}

.explanation-content {
    padding: 0 18px 18px;
    border-top: 1px solid var(--line);
}

/* Smooth scroll */
html {
    scroll-behavior: smooth;
}

/* Responsive */
@media (max-width: 900px) {
    .analysis-layout {
        grid-template-columns: 1fr;
    }
    
    .analysis-sidebar {
        position: static;
        max-height: none;
        order: -1; /* Показать сверху */
    }
    
    .sidebar-nav {
        flex-direction: row;
        overflow-x: auto;
        padding-bottom: 8px;
    }
    
    .sidebar-link {
        flex-shrink: 0;
        white-space: nowrap;
    }
}
```

#### 3.4. Добавить JavaScript для автоподсветки активного раздела
- [ ] Использовать Intersection Observer API
- [ ] Подсвечивать активный пункт при скролле
- [ ] Открывать details, если есть якорь в URL

**Файлы:**
- `candidate_trainer/static/candidate_trainer/js/trainer.js`

**JavaScript:**
```javascript
// Sidebar navigation highlight
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.analysis-sidebar');
    if (!sidebar) return;
    
    const sections = document.querySelectorAll('.analysis-content > .content-section');
    const links = document.querySelectorAll('.sidebar-link');
    
    // Intersection Observer для подсветки активного раздела
    const observerOptions = {
        root: null,
        rootMargin: '-80px 0px -60% 0px',
        threshold: 0
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');
                links.forEach(link => {
                    link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
                });
            }
        });
    }, observerOptions);
    
    sections.forEach(section => observer.observe(section));
    
    // Открыть details, если есть якорь в URL
    const hash = window.location.hash;
    if (hash && hash.startsWith('#explanation-')) {
        const details = document.querySelector(`details${hash}`);
        if (details) {
            details.open = true;
            details.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
});
```

#### 3.5. Обновить view для передачи счётчиков
- [ ] Подсчитать количество объяснений
- [ ] Передать в контекст шаблона

**Файлы:**
- `candidate_trainer/views.py` - функция `analysis_detail`

**Изменения:**
```python
# Подсчитать объяснения
explanations_count = sum(1 for as_ in analysis_skills if as_.explanation)

return render(
    request,
    "candidate_trainer/analysis_detail.html",
    {
        "analysis": analysis,
        "analysis_skills": analysis_skills,
        "active_sessions": active_sessions,
        "explanations_count": explanations_count,
    },
)
```

### Критерии приёмки
✅ Боковая панель с навигацией по разделам (sticky)  
✅ Автоподсветка активного раздела при скролле  
✅ Счётчики элементов в каждом разделе  
✅ Объяснения схлопнуты по умолчанию с превью  
✅ Плавный скролл к разделу при клике  
✅ Responsive: на мобилке sidebar превращается в горизонтальную навигацию  
✅ Якорь #explanation-{id} автоматически открывает нужное объяснение  

### Комментарии
_Пусто - этап не начат_

---

## Порядок реализации

1. **Этап 1** (простой, не затрагивает архитектуру)
2. **Этап 2** (ключевое изменение, требует миграции)
3. **Этап 3** (улучшение UX, независимо от предыдущих)

---

## Риски и зависимости

### Этап 1
- **Риски:** минимальные, только UI изменения
- **Зависимости:** нет

### Этап 2
- **Риски:** 
  - Миграция существующих данных (дедупликация)
  - Изменение логики может повлиять на существующие объяснения
- **Зависимости:** 
  - Требует тестирования на staging с реальными данными
  - Backup БД перед миграцией

### Этап 3
- **Риски:** минимальные, только фронтенд
- **Зависимости:** желательно после Этапа 2 (чтобы учесть новую структуру объяснений)

---

## Дополнительные улучшения (Future scope)

- Страница "Мои навыки" - список всех изученных навыков пользователя
- Ручное обновление объяснения через админку (admin action)
- Персональные объяснения (user IS NOT NULL) для кастомизации
- Экспорт объяснений в PDF/Markdown
- Статистика: сколько пользователей изучили каждый навык
- Поиск по объяснениям

---

## История изменений

| Дата | Версия | Изменение |
|------|--------|-----------|
| 23.10.2026 | 1.0 | Создан первоначальный план |
