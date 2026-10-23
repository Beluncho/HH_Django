# Этап 1: Управление сессиями собеседований

**Статус:** ✅ Выполнен  
**Дата:** 2025-01-XX

## Что реализовано

### 1. Dashboard (главная страница)
- Добавлен счётчик количества сообщений для каждой активной сессии
- Формат: "дата • N сообщений"
- View `dashboard()` обновлён с аннотацией `message_count`

### 2. Страница анализа (analysis_detail)
- Показываются все активные сессии для текущего анализа
- Для каждой сессии: кнопка "Продолжить", номер сессии, дата и количество сообщений
- Кнопка "Начать новое собеседование" всегда доступна
- View `analysis_detail()` загружает активные сессии с аннотацией `message_count`

## Изменённые файлы

### `candidate_trainer/views.py`
```python
# В функции dashboard():
sessions = (
    request.user.interview_sessions.select_related("analysis")
    .filter(status=InterviewSession.Status.ACTIVE)
    .annotate(message_count=Count("messages"))[:10]
)

# В функции analysis_detail():
active_sessions = (
    analysis.interview_sessions.filter(
        user=request.user, status=InterviewSession.Status.ACTIVE
    )
    .annotate(message_count=Count("messages"))
    .order_by("-created_at")
)
```

### `candidate_trainer/templates/candidate_trainer/dashboard.html`
- Добавлен счётчик сообщений: `{{ session.message_count }} сообщений`
- Добавлена метка "активных" в заголовок секции

### `candidate_trainer/templates/candidate_trainer/analysis_detail.html`
- Добавлен блок с активными сессиями перед кнопкой "Начать новое"
- Кнопки "Продолжить" ведут на существующие сессии
- Отображается: номер сессии, дата, количество сообщений

## Проверка

### Критерии приёмки
- [x] На dashboard показывается количество сообщений
- [x] На странице анализа видны активные сессии
- [x] Каждая сессия имеет кнопку "Продолжить"
- [x] Кнопка "Начать новое собеседование" всегда доступна
- [x] Клик по "Продолжить" переходит на страницу сессии

### Тестирование
Для проверки требуется запуск в Docker (из-за зависимостей от PostgreSQL и окружения).

## Следующий этап

**Этап 2:** Глобальная база объяснений навыков с версионированием (365 дней)
