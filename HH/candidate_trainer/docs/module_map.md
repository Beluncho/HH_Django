# Candidate Trainer: навигация по коду модуля

Карта модуля для быстрой ориентации в коде. Ссылки открываются на нужной строке.
Отсчёт путей — от `HH/candidate_trainer/`.

---

## 1. Архитектура модуля

**Основная идея:** отдельное Django-приложение внутри проекта HH_Django. Старые `hhapp` и `userapp` не затронуты — интеграция только через общие модели (`WebSiteUser`, опционально `Vacancy` для связи с внешними вакансиями).

**Структура:**
- **models.py** — 12 моделей данных: анализ вакансий, навыки, интервью, базы знаний, логи LLM
- **services/** — бизнес-логика, разделённая на небольшие модули (7 файлов)
- **views.py** — веб-интерфейс (9 представлений)
- **admin.py** — административный интерфейс Django для управления базами знаний
- **management/commands/** — CLI-команды для демо и экспериментов (5 команд)
- **tests/** — unit-тесты (9 тестовых модулей)

---

## 2. Модели данных

Все модели: [models.py](../models.py)

### Анализ вакансий
- **VacancyAnalysis** [:18](../models.py#L18) — запрос пользователя, статус, регион, результаты
- **HHVacancySnapshot** [:52](../models.py#L52) — сохранённая карточка вакансии с HH.ru
- **Skill** [:88](../models.py#L88) — канонический навык (нормализованное название)
- **AnalysisSkill** [:101](../models.py#L101) — связь анализа с навыком: частота, ранг, варианты написания

### Объяснения и базы знаний
- **SkillExplanation** [:123](../models.py#L123) — глобальное объяснение навыка (для всех пользователей)
- **KnowledgeCollection** [:141](../models.py#L141) — коллекция знаний (skill_core, interview, user_analytics)
  - Частичное уникальное ограничение [:163](../models.py#L163) — одна глобальная коллекция каждого типа
- **KnowledgeDocument** [:177](../models.py#L177) — документ в коллекции (методичка, статья, генерация)
- **KnowledgeChunk** [:201](../models.py#L201) — фрагмент документа с embedding для RAG-поиска

### Интервью
- **InterviewSession** [:228](../models.py#L228) — сессия собеседования, текущий навык, статус
- **InterviewMessage** [:262](../models.py#L262) — сообщение в диалоге (вопрос/ответ), привязка к навыку
- **InterviewInsight** [:286](../models.py#L286) — структурированная оценка ответа (баллы, пробелы, рекомендации)

### Журналирование
- **LLMRequestLog** [:324](../models.py#L324) — журнал вызовов LLM: операция, длительность, токены, ошибки

---

## 3. Сервисы (бизнес-логика)

Все сервисы: [services/](../services/)

### Анализ вакансий
- **hh_client.py** [:1](../services/hh_client.py#L1) — клиент HH.ru API
  - Поиск вакансий по запросу [:41](../services/hh_client.py#L41)
  - Получение полной карточки [:56](../services/hh_client.py#L56)
  - Обработка ошибок API [:35](../services/hh_client.py#L35)
- **normalization.py** [:1](../services/normalization.py#L1) — нормализация навыков
  - Извлечение навыков из карточки [:87](../services/normalization.py#L87)
  - Дедупликация внутри вакансии [:96](../services/normalization.py#L96)
  - Нормализация названия навыка [:21](../services/normalization.py#L21)
- **analysis.py** [:1](../services/analysis.py#L1) — оркестратор анализа
  - Точка входа `run_analysis` [:129](../services/analysis.py#L129)
  - Получение карточек вакансий [:166](../services/analysis.py#L166)
  - Обработка ошибок отдельных вакансий [:182](../services/analysis.py#L182)
  - Сохранение результата в базу [:195](../services/analysis.py#L195)
  - Агрегация частот навыков [:234](../services/analysis.py#L234)

### RAG и базы знаний
- **embeddings.py** [:1](../services/embeddings.py#L1) — векторные представления
  - `SentenceTransformerService` [:17](../services/embeddings.py#L17) — локальная модель на CPU
  - `HashEmbeddingService` [:83](../services/embeddings.py#L83) — тестовые embedding (быстрые, но бесполезные)
- **knowledge.py** [:1](../services/knowledge.py#L1) — работа с базами знаний
  - Создание/получение коллекции [:19](../services/knowledge.py#L19)
  - Поиск глобальной коллекции [:54](../services/knowledge.py#L54)
  - Индексация документа [:86](../services/knowledge.py#L86)
  - RAG-поиск по коллекции `KnowledgeRetriever.retrieve` [:237](../services/knowledge.py#L237)
  - Поиск «по навыку или общих» [:273](../services/knowledge.py#L273)
- **knowledge_import.py** [:1](../services/knowledge_import.py#L1) — импорт документов
  - Разбивка на фрагменты (chunking) [:122](../services/knowledge_import.py#L122)
  - Парсинг Markdown [:73](../services/knowledge_import.py#L73)

### LLM и промты
- **llm.py** [:1](../services/llm.py#L1) — клиент языковой модели
  - `get_llm_client` [:10](../services/llm.py#L10) — выбор провайдера (OpenAI/Anthropic)
  - Обработка ошибок [:72](../services/llm.py#L72)
  - Извлечение подсказки из ошибки [:45](../services/llm.py#L45)
- **llm_log.py** [:1](../services/llm_log.py#L1) — журналирование вызовов LLM
  - Контекстный менеджер `record_llm_call` [:12](../services/llm_log.py#L12)
  - Сохранение метрик и ошибок [:47](../services/llm_log.py#L47)
- **prompts.py** [:1](../services/prompts.py#L1) — промты для LLM
  - `explanation_prompt` [:72](../services/prompts.py#L72) — объяснение навыка
  - `initial_question_prompt` [:90](../services/prompts.py#L90) — первый вопрос интервью
  - `evaluation_prompt` [:110](../services/prompts.py#L110) — оценка ответа + следующий вопрос
  - Варианты промтов для экспериментов [:15](../services/prompts.py#L15)

### Интервью
- **interview.py** [:1](../services/interview.py#L1) — тестовое собеседование
  - Создание сессии `start_interview` [:97](../services/interview.py#L97)
  - Генерация первого вопроса `ensure_initial_question` [:128](../services/interview.py#L128)
  - Отправка ответа `submit_interview_answer` [:277](../services/interview.py#L277)
  - Выбор следующего навыка `_select_next_skill` [:225](../services/interview.py#L225) — ротация по топ-8
  - Индексация ответа в user_analytics [:246](../services/interview.py#L246)
  - Объяснение навыка `explain_skill` [:48](../services/interview.py#L48)

### Исключения
- **exceptions.py** [:1](../services/exceptions.py#L1) — типы ошибок модуля (7 классов)

---

## 4. Веб-интерфейс

- **Адреса:** [urls.py](../urls.py)
- **Представления:** [views.py](../views.py)
  - Dashboard (список анализов) [:29](../views.py#L29)
  - Детали анализа [:73](../views.py#L73)
  - Создание анализа [:112](../views.py#L112)
  - Запуск анализа [:127](../views.py#L127)
  - Объяснение навыка [:152](../views.py#L152)
  - Создание интервью [:163](../views.py#L163)
  - Детали интервью [:209](../views.py#L209)
  - Отправка ответа [:229](../views.py#L229)
  - Завершение интервью [:251](../views.py#L251)

- **Формы:** [forms.py](../forms.py)
  - Валидация запроса и региона [:26](../forms.py#L26)
  - Ответ в интервью [:46](../forms.py#L46)

- **Шаблоны:** [templates/candidate_trainer/](../templates/candidate_trainer/)
  - base.html — базовый шаблон с навигацией
  - dashboard.html — создание анализа + история + активные сессии
  - analysis_detail.html — обзор, навыки, объяснения, вакансии + sticky sidebar
  - interview.html — диалог + разбор ответов (insights)

- **Template tags:** [templatetags/trainer_filters.py](../templatetags/trainer_filters.py)
  - `render_markdown` [:14](../templatetags/trainer_filters.py#L14) — рендер Markdown с поддержкой списков
  - `strip_list_marker` [:29](../templatetags/trainer_filters.py#L29) — очистка маркеров для вложенного списка

- **Статика:** [static/candidate_trainer/](../static/candidate_trainer/)
  - css/trainer.css — дизайн модуля (оранжевая палитра, sticky sidebar, responsive)
  - js/trainer.js — индикатор работы форм (progress strip, busy state)

---

## 5. CLI-команды

Все команды: [management/commands/](../management/commands/)

- **check_llm.py** [:1](../management/commands/check_llm.py#L1) — проверка связи с LLM + запись в журнал
- **run_analysis_demo.py** [:1](../management/commands/run_analysis_demo.py#L1) — демо анализа вакансий без браузера
  - Документация: [command_run_analysis_demo.md](command_run_analysis_demo.md)
- **run_experiment.py** [:1](../management/commands/run_experiment.py#L1) — сравнение вариантов промтов
  - Документация: [command_run_experiment.md](command_run_experiment.md)
- **import_knowledge.py** [:1](../management/commands/import_knowledge.py#L1) — загрузка документа в базу знаний
- **reindex_embeddings.py** [:1](../management/commands/reindex_embeddings.py#L1) — пересчёт векторов при смене модели
- **create_test_interview.py** [:1](../management/commands/create_test_interview.py#L1) — заготовка для отладки

Общие утилиты команд: [management/demo_utils.py](../management/demo_utils.py)
- Проверка настроек и миграций [:33](../management/demo_utils.py#L33)

---

## 6. Тесты

Все тесты: [tests/](../tests/)

- **test_analysis.py** [:1](../tests/test_analysis.py#L1) — анализ вакансий
  - Успешный анализ с нормализацией навыков [:33](../tests/test_analysis.py#L33)
  - Дедупликация кеша анализов [:97](../tests/test_analysis.py#L97)
  - Обработка частичных сбоев [:139](../tests/test_analysis.py#L139)
- **test_interview.py** [:1](../tests/test_interview.py#L1) — интервью
  - Создание insight и приватной аналитики [:123](../tests/test_interview.py#L123)
  - Обработка ошибок LLM [:147](../tests/test_interview.py#L147)
  - Повторная попытка после сбоя [:166](../tests/test_interview.py#L166)
  - Ротация навыков [:237](../tests/test_interview.py#L237)
- **test_knowledge.py** [:1](../tests/test_knowledge.py#L1) — RAG и базы знаний
  - Создание коллекций [:18](../tests/test_knowledge.py#L18)
  - Индексация и поиск [:71](../tests/test_knowledge.py#L71)
  - Ограничение одной глобальной коллекции [:145](../tests/test_knowledge.py#L145)
- **test_llm.py** [:1](../tests/test_llm.py#L1) — вызовы LLM
  - Извлечение подсказки из ответа провайдера [:64](../tests/test_llm.py#L64)
  - Ключ API не попадает в ошибку [:117](../tests/test_llm.py#L117)
- **test_normalization.py** [:1](../tests/test_normalization.py#L1) — нормализация навыков
  - Дедупликация внутри вакансии [:22](../tests/test_normalization.py#L22)
  - Нормализация регистра и пунктуации [:47](../tests/test_normalization.py#L47)
- **test_prompts.py** [:1](../tests/test_prompts.py#L1) — промты
  - Варианты промтов для экспериментов [:7](../tests/test_prompts.py#L7)
- **test_template_filters.py** [:1](../tests/test_template_filters.py#L1) — template tags
  - Рендер Markdown с поддержкой списков [:30](../tests/test_template_filters.py#L30)
- **test_views.py** [:1](../tests/test_views.py#L1) — веб-интерфейс
  - Права доступа к анализам [:54](../tests/test_views.py#L54)
  - Создание и запуск анализа [:66](../tests/test_views.py#L66)
- **test_knowledge_import.py** [:1](../tests/test_knowledge_import.py#L1) — импорт документов
  - Chunking с overlap [:13](../tests/test_knowledge_import.py#L13)
  - Парсинг Markdown [:100](../tests/test_knowledge_import.py#L100)

Mock-объекты: [tests/fakes.py](../tests/fakes.py)
- `FakeHHClient` [:7](../tests/fakes.py#L7) — эмуляция HH.ru API
- `QueueLLMClient` [:26](../tests/fakes.py#L26) — предсказуемые ответы LLM
- `FailingLLMClient` [:48](../tests/fakes.py#L48) — эмуляция сбоев
- `FailingRetriever` [:53](../tests/fakes.py#L53) — проверка fallback без RAG

---

## 7. Административный интерфейс

- **admin.py** [:1](../admin.py#L1) — регистрация моделей в Django Admin
  - Загрузка документа через веб-форму [:136](../admin.py#L136)
  - Просмотр журнала LLM [:157](../admin.py#L157)

- **Кастомные шаблоны админки:**
  - [templates/admin/candidate_trainer/knowledge_import.html](../templates/admin/candidate_trainer/knowledge_import.html) — форма загрузки
  - [templates/admin/candidate_trainer/knowledgecollection/change_list.html](../templates/admin/candidate_trainer/knowledgecollection/change_list.html) — кнопка загрузки

---

## 8. Миграции

Все миграции: [migrations/](../migrations/)

- **0001_initial.py** [:1](../migrations/0001_initial.py#L1) — начальная схема (10 моделей)
- **0002_llmrequestlog.py** [:1](../migrations/0002_llmrequestlog.py#L1) — журнал LLM
- **0003_change_skill_explanation_to_global.py** [:1](../migrations/0003_change_skill_explanation_to_global.py#L1) — глобальные объяснения
  - RunPython миграция данных [:9](../migrations/0003_change_skill_explanation_to_global.py#L9)
- **0004_rename_...py** [:1](../migrations/0004_rename_candidate_t_skill_i_idx_candidate_t_skill_i_1945f4_idx.py#L1) — переименование индекса

---

## 9. Документация

Все документы: [docs/](../docs/)

- **command_run_analysis_demo.md** — описание команды анализа вакансий
- **command_run_experiment.md** — описание команды экспериментов с промтами
- **improvement_plan.md** — план улучшения модуля (этапы 1-4)
- **markdown_rendering.md** — объяснение рендера Markdown в шаблонах
- **stage1_session_management.md** — управление сессиями интервью
- **stage2_global_explanations.md** — глобальные объяснения навыков
- **stage3_sidebar_navigation.md** — sticky sidebar с навигацией
- **summary_all_stages.md** — сводка всех этапов разработки
- **testing_checklist.md** — чек-лист тестирования

---

## 10. Ключевые решения и паттерны

### Права доступа
- Все представления закрыты `@login_required` — [views.py:29](../views.py#L29), [:73](../views.py#L73), [:112](../views.py#L112), [:127](../views.py#L127), [:152](../views.py#L152), [:163](../views.py#L163), [:209](../views.py#L209), [:229](../views.py#L229), [:251](../views.py#L251)
- Проверка владельца анализа — [interview.py:53](../services/interview.py#L53)
- Нельзя смотреть незавершённый анализ — [interview.py:55](../services/interview.py#L55)

### Обработка ошибок
- Свои типы ошибок — [exceptions.py](../services/exceptions.py)
- Ошибки HH.ru → понятные сообщения — [hh_client.py:35](../services/hh_client.py#L35)
- Сбой одной вакансии не роняет анализ — [analysis.py:182](../services/analysis.py#L182)
- Причина сохраняется в базу — [analysis.py:294](../services/analysis.py#L294)
- Ошибки LLM не теряются — [llm_log.py:47](../services/llm_log.py#L47)
- Пользователь видит сообщение, а не traceback — [views.py:41](../views.py#L41)

### Частота навыков
Подсчёт в Python, а не в SQL — навыки дедуплицируются внутри вакансии [normalization.py:87](../services/normalization.py#L87), затем считается количество вакансий [analysis.py:234](../services/analysis.py#L234). Это требование из `AGENTS.md`.

### RAG-поиск
- Поиск «по навыку или общих» — [knowledge.py:273](../services/knowledge.py#L273)
- Fallback при пустой коллекции — [interview.py:119](../services/interview.py#L119)
- RAG опционален — если disabled или пусто, система работает без него

### Prompt engineering
- Системный промт — [prompts.py:4](../services/prompts.py#L4)
- Данные (вакансии, ответы пользователя) передаются в `<data>` — не смешиваются с инструкциями
- Ротация навыков: `next_skill` передаётся в промт **до** вызова LLM — [interview.py:342](../services/interview.py#L342)
- Варианты промтов для A/B тестов — [prompts.py:15](../services/prompts.py#L15)

### Журналирование LLM
Каждый вызов записывается через `record_llm_call` — [llm_log.py:12](../services/llm_log.py#L12):
- Операция, статус, провайдер, модель, длительность
- HTTP-код и тело ответа провайдера при сбое
- Расход токенов
- Тексты промтов и ответов **не** логируются (приватность)
- Запись журнала не роняет основную операцию

### Блокировки и транзакции
- Блокировка строки анализа при перезаписи — [analysis.py:195](../services/analysis.py#L195)
- `select_for_update` при создании insight — [interview.py:366](../services/interview.py#L366)

---

## 11. Интеграция с основным проектом

**Точки соприкосновения:**
- Настройки в [HH/settings.py:204](../../HH/settings.py#L204) — блок «Candidate trainer»
- URL-адреса в [HH/urls.py:29](../../HH/urls.py#L29) — префикс `/trainer/`
- Использование `settings.AUTH_USER_MODEL` — [models.py:19](../models.py#L19)
- `.gitignore:134` — кеш embedding-модели

**Что НЕ тронуто:**
- Старые приложения `hhapp` и `userapp` не переписаны
- API `/api/v0/` остался без изменений
- Старый клиент HH.ru [hhapp/services.py](../../hhapp/services.py) не используется

---

## 12. Команды для быстрого старта

```bash
# Проверка настроек
python manage.py check

# Применение миграций
python manage.py migrate

# Проверка связи с LLM
python manage.py check_llm

# Анализ вакансий (демо без браузера)
python manage.py run_analysis_demo "Python разработчик" --area 1

# Сравнение вариантов промтов
python manage.py run_experiment frequency

# Загрузка документа в базу знаний
python manage.py import_knowledge skill_core document.md --skill "Python"

# Тесты модуля
python manage.py test candidate_trainer

# Пересчёт embeddings после смены модели
python manage.py reindex_embeddings skill_core
```

**В браузере после входа:**

| Адрес | Описание |
|---|---|
| `/trainer/` | Dashboard: создание анализа, история, активные сессии |
| `/trainer/analysis/<id>/` | Детали анализа: навыки, объяснения, вакансии |
| `/trainer/interview/<id>/` | Тестовое собеседование: диалог + разбор ответов |
| `/admin/candidate_trainer/llmrequestlog/` | Журнал LLM: операции, длительность, токены, ошибки |
| `/admin/candidate_trainer/knowledgecollection/` | Управление базами знаний + загрузка документов |

---

## 13. Часто задаваемые вопросы

### Почему частота навыка считается в Python?
Внутри одной вакансии одинаковые навыки дедуплицируются — [normalization.py:87](../services/normalization.py#L87). Поэтому частота = количество вакансий, а не повторений слова. Это требование из `AGENTS.md`.

### Есть ли pgvector?
Нет. Для текущего объёма данных (десятки-сотни фрагментов) точного поиска достаточно. Индекс можно добавить позже при росте данных.

### Почему не Celery?
`AGENTS.md` разрешает начать с синхронного запуска. Точка входа одна — [analysis.py:129](../services/analysis.py#L129), позже её можно обернуть в Celery task без переписывания логики.

### Как работает ротация навыков?
`_select_next_skill` выбирает топ-8 навыков по рангу и циклически переключает: `skills[(completed_count + 1) % len(skills)]` — [interview.py:225](../services/interview.py#L225). `next_skill` передаётся в промт **до** вызова LLM, чтобы модель знала контекст следующего вопроса — [interview.py:342](../services/interview.py#L342).

### Где хранятся embeddings?
В базе PostgreSQL: [models.py:221](../models.py#L221) — `ArrayField(FloatField())`. Локальная модель sentence-transformers кешируется в `~/.cache/` — исключена из git в [.gitignore:134](../../../.gitignore#L134).

### Куда попадают тексты промтов?
Нигде. Журнал LLM сохраняет только метаданные (операция, длительность, токены) и тело ответа провайдера **при сбое**. Тексты промтов и ответов модели не логируются — [llm_log.py:47](../services/llm_log.py#L47).

### Как добавить новый вариант промта?
1. Добавить вариант в [prompts.py:15](../services/prompts.py#L15) — `EXPLANATION_VARIANTS` или `EVALUATION_VARIANTS`
2. Добавить инструкцию в словарь `_EXPLANATION_INSTRUCTIONS` или `_EVALUATION_INSTRUCTIONS`
3. Запустить эксперимент: `python manage.py run_experiment <variant>`

### Можно ли использовать другую LLM?
Да. Добавить класс-наследник `BaseLLMClient` в [llm.py](../services/llm.py) и выбрать через переменную окружения `LLM_PROVIDER`. Текущие: OpenAI, Anthropic.
