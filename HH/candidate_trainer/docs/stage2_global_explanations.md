# Этап 2: Глобальная база объяснений навыков

**Статус:** ✅ Выполнен  
**Дата:** 2025-01-XX

## Что реализовано

### 1. Изменение модели SkillExplanation

**Было:**
- `user` (обязательное) + `analysis_skill` → создавались дубликаты для каждого анализа
- Нет версионирования

**Стало:**
- `skill` (обязательное) + `user` (nullable) → глобальная база (user=NULL)
- `is_active` → версионирование, только одна активная версия на skill+user пару
- Уникальное ограничение: `unique_active_explanation_per_skill_user`
- Индекс: `(skill, user, is_active)`

### 2. Сервис для работы с глобальными объяснениями

Создан `services/explanation.py`:
- `get_or_create_global_explanation(skill, user)` — основная функция
- Проверка актуальности: если >= 365 дней, деактивирует старое и создаёт новое
- `_generate_explanation()` — генерация через LLM + RAG

### 3. Миграция данных

Создана миграция `0002_change_skill_explanation_to_global.py`:
1. Добавить поле `skill` (nullable)
2. Добавить поле `is_active`
3. Миграция данных: связать через `analysis_skill.skill`, дедуплицировать по canonical_name
4. Сделать `skill` обязательным
5. Сделать `user` nullable
6. Удалить `analysis_skill`
7. Добавить индексы и ограничения

**Логика дедупликации:**
- Группировка по `skill.canonical_name`
- Выбор самого свежего объяснения (max created_at)
- Помечается как глобальное (user=NULL, is_active=True)
- Остальные помечаются неактивными (is_active=False)

### 4. Обновление views и шаблонов

**views.py:**
- `analysis_detail()` загружает глобальные объяснения через `skill_id`
- `skill_explanation()` использует `get_or_create_global_explanation()`

**analysis_detail.html:**
- Кнопка "Посмотреть" если объяснение существует
- Кнопка "Объяснить" если объяснения нет
- Отображение через `item.global_explanation`
- Якорь `#skill-{{ item.skill.id }}`

## Изменённые файлы

### Новые файлы:
- `candidate_trainer/migrations/0002_change_skill_explanation_to_global.py`
- `candidate_trainer/services/explanation.py`

### Изменённые файлы:
- `candidate_trainer/models.py` — новая структура SkillExplanation
- `candidate_trainer/views.py` — использование глобальных объяснений
- `candidate_trainer/templates/candidate_trainer/analysis_detail.html` — UI для глобальных объяснений

## Проверка

### Критерии приёмки
- [x] Модель изменена на `skill + user(nullable) + is_active`
- [x] Миграция данных с дедупликацией
- [x] Сервис проверяет актуальность (365 дней)
- [x] UI показывает "Посмотреть" / "Объяснить"
- [x] Объяснения переиспользуются между пользователями
- [x] Старые версии деактивируются при обновлении

### Тестирование
Требуется запуск в Docker для:
- Применения миграции
- Проверки работы сервиса
- Тестирования UI

## Удалённый код

Старая функция `explain_skill()` в `services/interview.py` больше не используется для создания объяснений. Она создавала объяснения с привязкой к `analysis_skill`, что приводило к дублированию.

## Следующий этап

**Этап 3:** Sticky sidebar навигация с collapsible explanations
